
#include <iostream>

#include <unordered_map>
#include <memory>
#include <tuple>
#include <utility>
#include <set>
#include <vector>
#include <deque>
#include <cassert>
#include <stdint.h>

// For RWLocks
#include <pthread.h>

// switch map for array of pointers

namespace bk_tree
{
	typedef int64_t hash_type;
	typedef int64_t data_type;

	typedef std::pair<std::set<int64_t>, int64_t> search_ret;
	typedef std::tuple<bool, int64_t, int64_t> rebuild_ret;

	// Search return item. Contains [hash-value, item-data]
	typedef std::pair<hash_type, int64_t> hash_pair;
	typedef std::deque<hash_pair> return_deque;


	int64_t inline f_hamming(int64_t a_int, int64_t b_int);

	int64_t inline f_hamming(int64_t a_int, int64_t b_int)
	{
		/*
		Compute number of bits that are not common between `a` and `b`.
		return value is a plain integer
		*/

		// uint64_t x = (a_int ^ b_int);
		// __asm__(
		// 	"popcnt %0 %0  \n\t"// +r means input/output, r means intput
		// 	: "+r" (x) );

		// return x;
		uint64_t x = (a_int ^ b_int);

		return __builtin_popcountll (x);

	}



	class BK_Tree_Node
	{
		private:
			hash_type                                                 node_hash;

			// Unordered set is slower for small
			// numbers of n, which we mostly have.
			std::set<data_type>                                       node_data_items;

			std::vector<BK_Tree_Node *>                                children;

			rebuild_ret remove_internal(hash_type nodeHash, data_type nodeData, return_deque &ret_deq)
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
					if (this->node_data_items.count(nodeData) > 0)
					{
						// Remove the node data associated with the hash we want to remove
						this->node_data_items.erase(nodeData);
					}

					// If we've emptied out the node of data, return all our children so the parent can
					// graft the children into the tree in the appropriate place
					if (this->node_data_items.size() == 0)
					{
						// 1 deleted node, 0 moved nodes, return all children for reinsertion by parent
						// Parent will pop this node, and reinsert all it's children where apropriate
						this->get_contains(ret_deq);
						return rebuild_ret(true, 1, 0);
					}
					// node has data remaining, do not do any rebuilding
					return rebuild_ret(false, 1, 0);
				}

				int64_t selfDist = f_hamming(this->node_hash, nodeHash);

				// Removing is basically searching with a distance of zero, and
				// then doing operations on the search result.
				// As such, scan children where the edit distance between `self.nodeHash` and the target `nodeHash` == 0
				// Rebuild children where needed
				if (this->children[selfDist] != NULL)
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
						delete this->children[selfDist];
						this->children[selfDist] = NULL;
					}
				}
				return rebuild_ret(false, deleted, moved);
			}


			void insert_internal(hash_type nodeHash, data_type nodeData)
			{
				// std::cout << "Insert internal for hash: " << nodeHash << " nodeData: " << nodeData  << " onto node with hash: " << this->node_hash << std::endl;
				// If the current node has the same has as the data we're inserting,
				// add the data to the current node's data set
				if (nodeHash == this->node_hash)
				{
					this->node_data_items.insert(nodeData);
					return;
				}

				// otherwise, calculate the edit distance between the new phash and the current node's hash,
				// and either recursively insert the data, or create a new child node for the phash
				int distance = f_hamming(this->node_hash, nodeHash);

				if (this->children[distance] != NULL)
				{
					// std::cout << "Recursing into child-node for insert!" << std::endl;
					this->children[distance]->insert(nodeHash, nodeData);
				}
				else
				{
					// Construct in-place for extra fancyness
					// std::cout << "Creating child-node for insertion" << std::endl;
					this->children[distance] = new BK_Tree_Node(nodeHash, nodeData);
				}

			}


		protected:
			void search_internal(hash_type search_hash, int64_t distance, search_ret &ret)
			{
				// std::cout << "Doing hamming search" << std::endl;
				int64_t selfDist = f_hamming(this->node_hash, search_hash);
				// std::cout << "Searching node: " << this-> node_hash << " for " << search_hash << ", self-distance= " << selfDist << "." << std::endl;

				// Add self values if the current node is within the proper distance.
				if (selfDist <= distance)
				{

					for (const data_type &val: this->node_data_items)
					{
						// std::cout << "Found matching item at node: " << this->node_hash << " value: " << val << std::endl;
						ret.first.insert(val);
					}
				}

				ret.second += 1;

				int64_t posDelta = std::min((selfDist + distance), static_cast<int64_t>(64));
				int64_t negDelta = std::max((selfDist - distance), static_cast<int64_t>(0));

				for (int x = negDelta; x <= posDelta; x += 1)
				{
					if (this->children[x] != NULL)
					{
						// std::cout << "Decending into child-node for search" << std::endl;
						this->children[x]->search_internal(search_hash, distance, ret);
					}
				}

			}


		public:

			void get_contains(return_deque &ret_deq)
			{
				// For each item the node contains, push it back into the dequeu
				for (const int64_t i : this->node_data_items)
					ret_deq.push_back(hash_pair(this->node_hash, i));

				// Then, iterate over the item's children.
				for (const auto val : this->children)
					if (val != NULL)
						val->get_contains(ret_deq);

			}


			BK_Tree_Node(hash_type nodeHash, int64_t node_data)
			{
				// std::cout << "Instantiating BK_Tree_Node instance - Hash: " << nodeHash << " node_data: " << node_data << std::endl;
				this->node_data_items.insert(node_data);
				this->node_hash = nodeHash;

				// Child 0 is unused, because if the distance between the
				// current hash and the node hash is 0, it'll just be inserted onto the current
				// node's data.
				// We use a 65-ary tree just so the math is easier, leaking 8 bytes per node is kind of
				// irrelevant (I hope).
				this->children.assign(65, NULL);

			}

			~BK_Tree_Node()
			{
				for (auto val: this->children)
				{
					if (val != NULL)
						delete val;
				}
				// std::cout << "Destroying BK_Tree_Node instance" << std::endl;
			}

			void insert(hash_type nodeHash, int64_t nodeData)
			{
				this->insert_internal(nodeHash, nodeData);
			}


			std::vector<int64_t> remove(hash_type nodeHash, int64_t nodeData)
			{
				// Remove the matching hash. Insert any items that need to be re-added
				// into a deque for processing.
				return_deque ret_deq;
				auto rm_status = this->remove_internal(nodeHash, nodeData, ret_deq);


				int non_null_children = 0;
				for (size_t x = 0; x < this->children.size(); x += 1)
					if (this->children[x] != NULL)
						non_null_children += 1;

				// if the current node is empty, pull the first item from the new item list, and
				// set the current node to it's contained values.
				if (this->node_data_items.size() == 0 && ret_deq.empty() == false)
				{
					assert(non_null_children == 0);

					hash_pair new_root_content = ret_deq.front();
					ret_deq.pop_front();
					this->node_hash = new_root_content.first;
					this->node_data_items.insert(new_root_content.second);
				}

				// Rebuild any tree leaves that were damaged by the remove operation
				// by re-inserting their contents.
				for (const hash_pair i: ret_deq)
					this->insert(i.first, i.second);


				std::vector<int64_t> ret;
				ret.push_back(1 ? std::get<0>(rm_status) : 0);
				ret.push_back(std::get<1>(rm_status));
				ret.push_back(std::get<2>(rm_status));

				return ret;

			}

			search_ret search(hash_type baseHash, int distance)
			{
				search_ret ret;
				ret.second = 0;
				this->search_internal(baseHash, distance, ret);
				return ret;
			}
	};



	class BK_Tree
	{
		private:
			BK_Tree_Node      tree;
			pthread_rwlock_t lock_rw;


		public:

			BK_Tree(hash_type nodeHash, data_type node_id)
				: tree(nodeHash, node_id)
			{
				// std::cout << "Instantiating BK_Tree instance" << std::endl;
				this->lock_rw = PTHREAD_RWLOCK_INITIALIZER;
				int ret = pthread_rwlock_init(&(this->lock_rw), NULL);
				if (ret != 0)
				{
					std::cerr << "Error initializing pthread rwlock!" << std::endl;
				}
				assert(ret == 0);
			}

			~BK_Tree()
			{
				// std::cout << "Destroying BK_Tree instance" << std::endl;
			}

			void insert(hash_type nodeHash, data_type nodeData)
			{
				this->get_write_lock();
				this->tree.insert(nodeHash, nodeData);
				this->free_write_lock();
			}

			void unlocked_insert(hash_type nodeHash, data_type nodeData)
			{
				this->tree.insert(nodeHash, nodeData);
			}


			std::vector<int64_t> remove(hash_type nodeHash, data_type nodeData)
			{
				this->get_write_lock();
				auto rm_status = this->tree.remove(nodeHash, nodeData);

				// bool rebuild = rm_status[0]; // Rebuilding is handled in tree.remove()
				int deleted  = rm_status[1];
				int moved    = rm_status[2];

				this->free_write_lock();
				std::vector<int64_t> ret(2);
				ret[0] = deleted;
				ret[1] = moved;
				return ret;
			}

			search_ret getWithinDistance(hash_type baseHash, int distance)
			{
				// std::cout << "Get within distance!" << std::endl;
				this->get_read_lock();
				auto ret = this->tree.search(baseHash, distance);
				this->free_read_lock();
				return ret;
			}

			return_deque get_all(void)
			{
				return_deque ret;
				this->get_read_lock();
				this->tree.get_contains(ret);
				this->free_read_lock();
				return ret;
			}

			void get_read_lock(void)
			{
				pthread_rwlock_rdlock(&(this->lock_rw));
			}
			void get_write_lock(void)
			{
				pthread_rwlock_wrlock(&(this->lock_rw));

			}

			void free_read_lock(void)
			{
				pthread_rwlock_unlock(&(this->lock_rw));
			}
			void free_write_lock(void)
			{
				pthread_rwlock_unlock(&(this->lock_rw));
			}


	};



}