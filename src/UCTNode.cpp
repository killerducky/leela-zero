/*
    This file is part of Leela Zero.
    Copyright (C) 2017 Gian-Carlo Pascutto

    Leela Zero is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Leela Zero is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Leela Zero.  If not, see <http://www.gnu.org/licenses/>.
*/

#include "config.h"

#include <cassert>
#include <cstdio>
#include <cstdint>
#include <algorithm>
#include <cmath>
#include <functional>
#include <iterator>
#include <limits>
#include <numeric>
#include <utility>
#include <vector>

#include "UCTNode.h"
#include "FastBoard.h"
#include "FastState.h"
#include "GTP.h"
#include "GameState.h"
#include "Network.h"
#include "Random.h"
#include "Utils.h"

using namespace Utils;

UCTNode::UCTNode(int vertex, float score) : m_move(vertex), m_score(score) {
}

bool UCTNode::first_visit() const {
    return m_visits == 0;
}

SMP::Mutex& UCTNode::get_mutex() {
    return m_nodemutex;
}

bool UCTNode::create_children(std::atomic<int>& nodecount,
                              GameState& state,
                              float& eval) {
    // check whether somebody beat us to it (atomic)
    if (has_children()) {
        return false;
    }
    // acquire the lock
    LOCK(get_mutex(), lock);
    // no successors in final state
    if (state.get_passes() >= 2) {
        return false;
    }
    // check whether somebody beat us to it (after taking the lock)
    if (has_children()) {
        return false;
    }
    // Someone else is running the expansion
    if (m_is_expanding) {
        return false;
    }
    // We'll be the one queueing this node for expansion, stop others
    m_is_expanding = true;
    lock.unlock();

    // TODO: Network/NNCache should remember which rotations have been done.
    m_last_rotation = Random::get_Rng().randfix<8>();
    const auto raw_netlist = Network::get_scored_moves(
        &state, Network::Ensemble::DIRECT, m_last_rotation, true);
    assert(m_num_rotations == 0);
    m_num_rotations = 1;

    // DCNN returns winrate as side to move
    m_net_eval = raw_netlist.second;
    const auto to_move = state.board.get_to_move();
    // our search functions evaluate from black's point of view
    if (state.board.white_to_move()) {
        m_net_eval = 1.0f - m_net_eval;
    }
    eval = m_net_eval;

    std::vector<Network::scored_node> nodelist;

    auto legal_sum = 0.0f;
    for (const auto& node : raw_netlist.first) {
        auto vertex = node.second;
        if (state.is_move_legal(to_move, vertex)) {
            nodelist.emplace_back(node);
            legal_sum += node.first;
        }
    }

    if (legal_sum > std::numeric_limits<float>::min()) {
        // re-normalize after removing illegal moves.
        for (auto& node : nodelist) {
            node.first /= legal_sum;
        }
    } else {
        // This can happen with new randomized nets.
        auto uniform_prob = 1.0f / nodelist.size();
        for (auto& node : nodelist) {
            node.first = uniform_prob;
        }
    }

    link_nodelist(nodecount, nodelist);
    return true;
}

float UCTNode::do_next_rotation(GameState& state) {
    // TODO: thread safe
    auto move = state.move_to_text(get_move());
    myprintf("debug dnr %4s v:%d\n", move.c_str(), get_visits());

    assert(m_num_rotations > 0 && m_num_rotations < 8);
    // After the initial random choice, just walk in order
    m_last_rotation = (m_last_rotation + 1) % 8;

    // TODO: Network/NNCache should remember which rotations have been done.
    const auto raw_netlist = Network::get_scored_moves(
        &state, Network::Ensemble::DIRECT, m_last_rotation, true);

    // DCNN returns winrate as side to move
    auto this_net_eval = raw_netlist.second;
    const auto to_move = state.board.get_to_move();
    // our search functions evaluate from black's point of view
    if (state.board.white_to_move()) {
        this_net_eval = 1.0f - this_net_eval;
    }
    // Average in new eval
    auto orig_eval = m_net_eval;
    m_net_eval =
        (m_num_rotations * m_net_eval + this_net_eval)
        / (m_num_rotations + 1);
    myprintf("debug value orig:%5.2f this:%5.2f diff:%5.2f avg:%5.2f\n",
        orig_eval*100.0f, this_net_eval*100.0f, (orig_eval-this_net_eval)*100.0f, m_net_eval*100.0f);

    std::vector<Network::scored_node> nodelist;

    auto legal_sum = 0.0f;
    for (const auto& node : raw_netlist.first) {
        auto vertex = node.second;
        if (state.is_move_legal(to_move, vertex)) {
            nodelist.emplace_back(node);
            legal_sum += node.first;
        }
    }

    if (legal_sum > std::numeric_limits<float>::min()) {
        // re-normalize after removing illegal moves.
        for (auto& node : nodelist) {
            node.first /= legal_sum;
        }
    } else {
        // This can happen with new randomized nets.
        auto uniform_prob = 1.0f / nodelist.size();
        for (auto& node : nodelist) {
            node.first = uniform_prob;
        }
    }

    // Average in new scores
    assert(m_has_children);
    for (auto& node : nodelist) {
        auto found = false;
        for (auto& child : m_children) {
            if (node.second == child->get_move()) {
                auto orig_score = child->m_score;
                child->m_score =
                    (m_num_rotations * child->m_score + node.first)
                    / (m_num_rotations + 1);
                auto move = state.move_to_text(child->get_move());
                myprintf("debug score %4s orig:%5.2f this:%5.2f diff:%5.2f avg:%5.2f\n",
                    move.c_str(), orig_score*100.0f, node.first*100.0f, (orig_score-node.first)*100.0f, child->m_score*100.0f);
                found = true;
                break;
            }
        }
        assert(found);
    }
    m_num_rotations++;

    // Backup the new eval only
    return this_net_eval;
}

void UCTNode::link_nodelist(std::atomic<int>& nodecount,
                            std::vector<Network::scored_node>& nodelist) {
    if (nodelist.empty()) {
        return;
    }

    // Use best to worst order, so highest go first
    std::stable_sort(rbegin(nodelist), rend(nodelist));

    LOCK(get_mutex(), lock);

    m_children.reserve(nodelist.size());
    for (const auto& node : nodelist) {
        m_children.emplace_back(
            std::make_unique<UCTNode>(node.second, node.first)
        );
    }

    nodecount += m_children.size();
    m_has_children = true;
}

const std::vector<UCTNode::node_ptr_t>& UCTNode::get_children() const {
    return m_children;
}


int UCTNode::get_move() const {
    return m_move;
}

void UCTNode::virtual_loss() {
    m_virtual_loss += VIRTUAL_LOSS_COUNT;
}

void UCTNode::virtual_loss_undo() {
    m_virtual_loss -= VIRTUAL_LOSS_COUNT;
}

void UCTNode::update(float eval) {
    m_visits++;
    accumulate_eval(eval);
}

bool UCTNode::has_children() const {
    return m_has_children;
}

float UCTNode::get_score() const {
    return m_score;
}

void UCTNode::set_score(float score) {
    m_score = score;
}

int UCTNode::get_visits() const {
    return m_visits;
}

int UCTNode::get_num_rotations() const {
    return m_num_rotations;
}

int UCTNode::get_last_rotation() const {
    return m_last_rotation;
}

float UCTNode::get_eval(int tomove) const {
    // Due to the use of atomic updates and virtual losses, it is
    // possible for the visit count to change underneath us. Make sure
    // to return a consistent result to the caller by caching the values.
    auto virtual_loss = int{m_virtual_loss};
    auto visits = get_visits() + virtual_loss;
    assert(visits > 0);
    auto blackeval = get_blackevals();
    if (tomove == FastBoard::WHITE) {
        blackeval += static_cast<double>(virtual_loss);
    }
    auto score = static_cast<float>(blackeval / (double)visits);
    if (tomove == FastBoard::WHITE) {
        score = 1.0f - score;
    }
    return score;
}

float UCTNode::get_net_eval(int tomove) const {
    if (tomove == FastBoard::WHITE) {
        return 1.0f - m_net_eval;
    }
    return m_net_eval;
}

double UCTNode::get_blackevals() const {
    return m_blackevals;
}

void UCTNode::accumulate_eval(float eval) {
    atomic_add(m_blackevals, (double)eval);
}

UCTNode* UCTNode::uct_select_child(int color) {
    UCTNode* best = nullptr;
    auto best_value = -1000.0;

    LOCK(get_mutex(), lock);

    // Count parentvisits manually to avoid issues with transpositions.
    auto total_visited_policy = 0.0f;
    auto parentvisits = size_t{0};
    for (const auto& child : m_children) {
        if (child->valid()) {
            parentvisits += child->get_visits();
            if (child->get_visits() > 0) {
                total_visited_policy += child->get_score();
            }
        }
    }

    auto numerator = std::sqrt((double)parentvisits);
    auto fpu_reduction = cfg_fpu_reduction * std::sqrt(total_visited_policy);
    // Estimated eval for unknown nodes = original parent NN eval - reduction
    auto fpu_eval = get_net_eval(color) - fpu_reduction;

    for (const auto& child : m_children) {
        if (!child->active()) {
            continue;
        }

        float winrate = fpu_eval;
        if (child->get_visits() > 0) {
            winrate = child->get_eval(color);
        }
        auto psa = child->get_score();
        auto denom = 1.0 + child->get_visits();
        auto puct = cfg_puct * psa * (numerator / denom);
        auto value = winrate + puct;
        assert(value > -1000.0);

        if (value > best_value) {
            best_value = value;
            best = child.get();
        }
    }

    assert(best != nullptr);
    return best;
}

class NodeComp : public std::binary_function<UCTNode::node_ptr_t&,
                                             UCTNode::node_ptr_t&, bool> {
public:
    NodeComp(int color) : m_color(color) {};
    bool operator()(const UCTNode::node_ptr_t& a,
                    const UCTNode::node_ptr_t& b) {
        // if visits are not same, sort on visits
        if (a->get_visits() != b->get_visits()) {
            return a->get_visits() < b->get_visits();
        }

        // neither has visits, sort on prior score
        if (a->get_visits() == 0) {
            return a->get_score() < b->get_score();
        }

        // both have same non-zero number of visits
        return a->get_eval(m_color) < b->get_eval(m_color);
    }
private:
    int m_color;
};

void UCTNode::sort_children(int color) {
    LOCK(get_mutex(), lock);
    std::stable_sort(rbegin(m_children), rend(m_children), NodeComp(color));
}

UCTNode& UCTNode::get_best_root_child(int color) {
    LOCK(get_mutex(), lock);
    assert(!m_children.empty());

    return *(std::max_element(begin(m_children), end(m_children),
                              NodeComp(color))->get());
}

size_t UCTNode::count_nodes() const {
    auto nodecount = size_t{0};
    if (m_has_children) {
        nodecount += m_children.size();
        for (auto& child : m_children) {
            nodecount += child->count_nodes();
        }
    }
    return nodecount;
}

void UCTNode::invalidate() {
    m_status = INVALID;
}

void UCTNode::set_active(const bool active) {
    if (valid()) {
        m_status = active ? ACTIVE : PRUNED;
    }
}

bool UCTNode::valid() const {
    return m_status != INVALID;
}

bool UCTNode::active() const {
    return m_status == ACTIVE;
}
