


#include <unordered_map>
#include <memory>
#include <tuple>
#include <utility>
#include <set>
#include <vector>
#include <deque>
#include <cassert>
#include <stdint.h>




namespace bk_tree
{
	typedef std::pair<std::set<int64_t>, int64_t> search_ret;
	typedef std::tuple<bool, int64_t, int64_t> rebuild_ret;

	// Search return item. Contains [hash-value, item-data]
	typedef std::pair<int64_t, int64_t> hash_pair;
	typedef std::deque<hash_pair> return_deque;

	int64_t hamming(int64_t a_int, int64_t b_int);

	int64_t hamming(int64_t a_int, int64_t b_int)
	{
		/*
		Compute number of bits that are not common between `a` and `b`.
		return value is a plain integer
		*/

		int tot = 0;

		// Messy explicit casting to work around the fact that
		// >> on a signed number is arithmetic, rather then logical,
		// which means that >> on -1 results in -1 (it shifts in the sign
		// value). This was breaking comparisons since we're checking if
		// x > 0 (it could be negative if the numbers are signed.)

		uint64_t a = static_cast<uint64_t>(a_int);
		uint64_t b = static_cast<uint64_t>(b_int);

		uint64_t x;
		x = (a ^ b);

		while (x > 0)
		{
			tot += x & 1;
			x >>= 1;
		}
		return tot;
	}


	class BK_Tree_Node
	{
		private:
			int64_t                                                 node_hash;

			// Unordered set is slower for small
			// numbers of n, which we mostly have.
			std::set<int64_t>                                       node_data_items;

			// We have to have a shared_ptr because
			// unordered_map cannot have members with incomplete types.
			std::unordered_map<int, std::shared_ptr<BK_Tree_Node> > children;

			rebuild_ret remove_internal(int64_t nodeHash, int64_t nodeData, return_deque &ret_deq)
			{
				// Remove node with hash `nodeHash` and accompanying data `nodeData` from the tree.
				// Returns list of children that must be re-inserted (or false if no children need to be updated),
				// number of nodes deleted, and number of nodes that were moved as a 3-tuple.

				int64_t deleted = 0;
				int64_t moved   = 0;

				// If the node we're on matches the hash we want to delete exactly:
				if (nodeHash == this->node_hash)
				{
					// Validate we have the
					if (this->node_data_items.count(nodeHash) > 0)
					{
						// Remove the node data associated with the hash we want to remove
						this->node_data_items.erase(nodeHash);
					}

					// If we've emptied out the node of data, return all our children so the parent can
					// graft the children into the tree in the appropriate place
					if (this->children.empty())
					{
						// 1 deleted node, 0 moved nodes, return all children for reinsertion by parent
						// Parent will pop this node, and reinsert all it's children where apropriate
						this->get_contains(ret_deq);
						return rebuild_ret(true, 1, 0);
					}
					// node has data remaining, do not do any rebuilding
					return rebuild_ret(false, 1, 0);
				}

				int64_t selfDist = hamming(this->node_hash, nodeHash);

				// Removing is basically searching with a distance of zero, and
				// then doing operations on the search result.
				// As such, scan children where the edit distance between `self.nodeHash` and the target `nodeHash` == 0
				// Rebuild children where needed
				if (this->children.count(selfDist) > 0)
				{
					rebuild_ret removed = this->children[selfDist]->remove_internal(nodeHash, nodeData, ret_deq);

					// moveChildren, childDeleted, childMoved = self.children[selfDist].remove(nodeHash, nodeData);

					bool remove_child = std::get<0>(removed);
					deleted          += std::get<1>(removed);
					moved            += std::get<2>(removed);

					// If the child returns children, it means the child no longer contains any unique data, so it
					// needs to be deleted. As such, pop it from the tree
					// It's children will be re-inserted as the last step in removal.
					if (remove_child)
					{
						this->children.erase(selfDist);
					}
				}
				return rebuild_ret(false, deleted, moved);
			}

			void get_contains(return_deque &ret_deq)
			{
				// For each item the node contains, push it back into the dequeu
				for (const uint64_t i : this->node_data_items)
					ret_deq.push_back(hash_pair(this->node_hash, i));

				// Then, iterate over the item's children.
				for (const auto val : this->children)
					val.second->get_contains(ret_deq);

			}


			void insert_internal(int64_t nodeHash, int64_t nodeData)
			{
				this->get_write_lock();
				// If the current node has the same has as the data we're inserting,
				// add the data to the current node's data set
				if (nodeHash == this->node_hash)
				{
					this->node_data_items.insert(node_hash);
					return;
				}

				// otherwise, calculate the edit distance between the new phash and the current node's hash,
				// and either recursively insert the data, or create a new child node for the phash
				int distance = hamming(this->node_hash, nodeHash);

				if (this->children.count(distance) > 0)
				{
					// Construct in-place for extra fancyness
					this->children.emplace(distance, std::make_shared<BK_Tree_Node>(nodeHash, nodeData));
				}
				else
				{
					this->children.at(distance)->insert(nodeHash, nodeData);
				}

			}


			void get_read_lock(void)
			{

			}
			void get_write_lock(void)
			{

			}

			void free_read_lock(void)
			{

			}
			void free_write_lock(void)
			{

			}


		public:


			BK_Tree_Node(int64_t nodeHash, int64_t node_id)
			{
				this->node_data_items.insert(node_id);
				this->node_hash = node_hash;
			}

			void insert(int64_t nodeHash, int64_t nodeData)
			{
				this->get_write_lock();
				this->insert_internal(nodeHash, nodeData);
				this->free_write_lock();
			}


			rebuild_ret remove(int64_t nodeHash, int64_t nodeData)
			{
				this->get_write_lock();
				// Remove the matching hash. Insert any items that need to be re-added
				// into a deque for processing.
				return_deque ret_deq;
				auto rm_status = this->remove_internal(nodeHash, nodeData, ret_deq);

				// Rebuild any tree leaves that were damaged by the remove operation
				// by re-inserting their contents.
				for (const hash_pair i: ret_deq)
					this->insert(i.first, i.second);

				this->free_write_lock();
				return rm_status;

			}


			search_ret getWithinDistance(int64_t baseHash, int distance)
			{
				this->get_read_lock();
				search_ret ret;
				ret.second = 0;
				this->free_read_lock();
				return ret;
			}
	};
}