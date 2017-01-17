#include <iostream>
#include <atomic>

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


namespace BK_Tree_Ns
{
	typedef int64_t hash_type;
	typedef int64_t data_type;

	typedef std::pair<std::set<int64_t>, int64_t> search_ret;
	typedef std::tuple<bool, int64_t, int64_t> rebuild_ret;

	// Search return item. Contains [hash-value, item-data]
	typedef std::pair<hash_type, int64_t> hash_pair;
	typedef std::deque<hash_pair> return_deque;


	int64_t inline f_hamming(int64_t a_int, int64_t b_int);

	/**
	 * @brief Compute the hamming distance, e.g. the number of differing
	 *        bits between two values, in the fastest manner possible.
	 *
	 * @param a_int bitfield 1 for distance calculation
	 * @param b_int bitfield 2 for distance calculation
	 *
	 * @return number of differing bits between the two values. Possible
	 *         return values are 0-64, as the parameters are 64 bit integers.
	 */
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

			const int tree_aryness;

			/**
			 * Bitmapped hash value for the node.
			 */
			hash_type                                                 node_hash;

			/**
			 * Data values associated with the current node. In my use, they're generally
			 * database-ID values as int64_t.
			 */
			std::set<data_type>                                       node_data_items;
			// Unordered set is slower for small
			// numbers of n, which we mostly have.

			/**
			 * Vector of pointers to children. Non-present children are indicated
			 * by a pointer value of NULL, present children are non-NULL.
			 * Vector size is 65, for an allowable edit-distance range of
			 * 0-64 (0 is functionally not used).
			 */
			std::vector<BK_Tree_Node *>                                children;

			/**
			 * @brief Internal item removal function. Removes a hash-data pair from the tree
			 *        and does any associated required tree-rebuilding that is required
			 *        as a function of the changes.
			 *
			 * @detail Note that re-insertion of parentless-nodes is actually handled by
			 *         BK_Tree_Node::remove, as it made the architecture design considerably
			 *         simpler, and node removal is not often done.
			 *         Rather then trying to do in-place re-insertion as soon as a valid parent
			 *         is reached, they're simply all propigated back up to the root node
			 *         and re-inserted from there, because that way there only
			 *         has to be a single point where re-insertion is done, and it can
			 *         use the same code-paths as normal insertion.
			 *
			 * @param nodeHash hash to search for.
			 * @param nodeData data associated with hash.
			 * @param ret_deq reference to a `return_deque` into which any parentless-node's data
			 *                is copied into for re-insertion.
			 * @return std::vector<int64_t> containing 3 status values.
			 *         The first is a boolean cast to an int, indicating
			 *         whether the direct child node is empty, and should
			 *         be deleted (with it's children re-inserted).
			 *
			 *         The second is a count of the number of children
			 *         that were actually deleted by the remove call (which
			 *         should really only ever be 1).
			 *         The third is the number of child-nodes that had to be re-inserted to
			 *         accomodate any deletion of any nodes.
			 */
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


			/**
			 * @brief Recursively find and insert a hash-data pair into the proper
			 *        node, creating it if necessary.
			 *
			 * @param nodeHash hash for data that is being inserted.
			 * @param nodeData data that accompanies inserted hash.
			 */
			void insert_internal(hash_type nodeHash, data_type nodeData)
			{
				// If the current node has the same hash as the data we're inserting,
				// add the data to the current node's data set
				if (nodeHash == this->node_hash)
				{
					this->node_data_items.insert(nodeData);
					return;
				}

				// otherwise, calculate the edit distance between the new phash and the current node's hash,
				// and either recursively insert the data, or create a new child node for the phash
				int distance = f_hamming(this->node_hash, nodeHash);


				if (this->children[distance] != NULL) // If we have a node, descend into it and try inserting it there.
				{
					this->children[distance]->insert(nodeHash, nodeData);
				}
				else // Otherwise, construct the new node for the data.
				{
					// Construct in-place for extra fancyness
					this->children[distance] = new BK_Tree_Node(nodeHash, nodeData);
				}

			}


			/**
			 * @brief Internals: Search function.
			 * @details Searches tree recursively for items within `distance` hamming
			 *          edit distance of `search_hash`. Found items are written into
			 *          the `&search_ret` reference.
			 *
			 * @param search_hash base hash to use for searching.
			 * @param distance Edit distance to search.
			 * @param ret Reference to deque into which found results are placed.
			 */
			void search_internal(hash_type search_hash, int64_t distance, search_ret &ret)
			{
				int64_t selfDist = f_hamming(this->node_hash, search_hash);

				// Add self values if the current node is within the proper distance.
				if (selfDist <= distance)
				{
					for (const data_type &val: this->node_data_items)
					{
						// std::cout << "Inserting self into return: " << val << " hash: " << this->node_hash << "." << std::endl;
						ret.first.insert(val);
					}
				}

				// std::cout << "Items in return: " << ret.first.size() << "." << std::endl;
				ret.second += 1;

				// Search scope is self_distance - search_distance <-> self_distance + search_distance,
				// as hamming distance is a metric space and obeys triangle inequalities.
				// We also clamp the search space to the bounds of our
				// index.
				int64_t posDelta = std::min((selfDist + distance), static_cast<int64_t>(64));
				int64_t negDelta = std::max((selfDist - distance), static_cast<int64_t>(1));

				// For each child within our search scope, if the child is present (non-NULL),
				// recursively search into that child.
				for (int_fast8_t x = negDelta; x <= posDelta; x += 1)
				{
					if (this->children[x] != NULL)
					{
						this->children[x]->search_internal(search_hash, distance, ret);
					}
				}

			}


		public:
			/**
			 * @brief Create a BK_Tree_Node containing the specified hash and data pair.
			 *
			 * @param nodeHash hash for node.
			 * @param node_data data associated with hash.
			 */
			BK_Tree_Node(hash_type nodeHash, int64_t node_data)
				: tree_aryness(65)
			{
				// std::cout << "Instantiating BK_Tree_Node instance - Hash: " << nodeHash << " node_data: " << node_data << std::endl;
				this->node_data_items.insert(node_data);
				this->node_hash = nodeHash;

				// Child 0 is unused, because if the distance between the
				// current hash and the node hash is 0, it'll just be inserted onto the current
				// node's data.
				// We use a 65-ary tree just so the math is easier, leaking 8 bytes per node is kind of
				// irrelevant (I hope).
				this->children.assign(this->tree_aryness, NULL);

			}

			int clear_node(void)
			{
				int cleared = 1;
				for (int x = 0; x < this->tree_aryness; x += 1)
				{
					if (this->children[x] != NULL)
					{
						// std::cout << "Deleting node " << (uint64_t) val << std::endl;
						cleared += this->children[x]->clear_node();
						delete this->children[x];
						this->children[x] = NULL;
					}
				}
				return cleared;
			}

			/**
			 * @brief Delete a node. This will explicitly delete any
			 *        children of the node as well.
			 */
			~BK_Tree_Node()
			{
				this->clear_node();
			}

			/**
			 * @brief Insert a hash<->data pair into the tree.
			 * @details Inserts a hash<->data pair into the tree.
			 *
			 * @param nodeHash node-hash to insert.
			 * @param nodeData data associated with the node-hash.
			 */
			void insert(hash_type nodeHash, int64_t nodeData)
			{
				this->insert_internal(nodeHash, nodeData);
			}


			/**
			 * @brief Given the hash and data-value for a item,
			 *        find and remove it from the tree.
			 * @details Removes an item from the tree by hash and
			 *          id. This may involve reconstructing up to
			 *          the entire tree, in a worst-case circumstance.
			 *
			 *          If the specified hash<->data pair is not found,
			 *          nothing will be done, and no error will be raised.
			 *
			 * @param nodeHash hash to remove
			 * @param nodeData id to remove
			 *
			 * @return std::vector<int64_t> containing 3 status values.
			 *         The first is a boolean cast to an int, indicating
			 *         whether the direct child node is empty, and should
			 *         be deleted (with it's children re-inserted).
			 *
			 *         The second is a count of the number of children
			 *         that were actually deleted by the remove call (which
			 *         should really only ever be 1).
			 *         The third is the number of child-nodes that had to be re-inserted to
			 *         accomodate any deletion of any nodes.
			 */
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


				// Pack up the return value.
				std::vector<int64_t> ret;
				ret.push_back(1 ? std::get<0>(rm_status) : 0);
				ret.push_back(std::get<1>(rm_status));
				ret.push_back(std::get<2>(rm_status));

				return ret;

			}

			/**
			 * @brief Search the tree for items within a
			 *        certain distance of a specified hash.
			 * @details Searches the tree recursively for
			 *          all items within a specified hamming distance
			 *          of the passed parameter.
			 *
			 * @param baseHash Hash-value to find items similar to.
			 * @param distance Maximum allowed Hamming distance between
			 *                 the specified hash and returned
			 *                 similar values.
			 *
			 * @return std::pair<std::set<int64_t>, int64_t>, where the
			 *         first item is a set of item_id values for each matched
			 *         similar items, and the second value is the number
			 *         of tree nodes the search had to touch to return
			 *         the first value (for diagnostic purposes).
			 */
			search_ret search(hash_type baseHash, int distance)
			{
				search_ret ret;
				ret.first.clear();
				// std::cout << "Search call! " << ret.first << "." << std::endl;
				ret.second = 0;
				this->search_internal(baseHash, distance, ret);

				// std::cout << "Search return: ";
				// for (auto& tmp : ret.first)
				// {
				// 	std::cout << tmp << ", ";
				// }
				// std::cout << "." << std::endl;

				return ret;
			}

			/**
			 * @brief Get all items in tree
			 * @details Fetches all contained items in the tree into
			 *          a `return_deque` passed by reference.
			 *          This is a non-destructive operation, it makes no changes to the
			 *          tree.
			 *
			 * @param ret_deq Reference to a deque<hash_pair>, where has_pair is
			 *                a std::pair<hash_type, int64_t> containing the item hash
			 *                and the item id respectively.
			 */
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



	};


	/**
	 * @brief General use-class for managing a tree of BK_Tree_Node nodes.
	 *        Provides parallel-access locking.
	 *
	 */
	class BK_Tree
	{
		private:
			BK_Tree_Node*      tree;
			pthread_rwlock_t lock_rw;


			// We track attempts to acquire the locks so we can detect accidental recursions.
			std::atomic<int>                                           recursed;

		public:

			/**
			 * @brief Construct a BK_Tree starting with specified node_values.
			 *        Also sets up the required RW locks an associated plumbing.
			 *
			 * @param nodeHash hash-value for the root of the tree.
			 * @param node_id associated data-value for the tree root.
			 */
			BK_Tree()
				: tree(NULL)
			{
				this->lock_rw = PTHREAD_RWLOCK_INITIALIZER;
				int ret = pthread_rwlock_init(&(this->lock_rw), NULL);
				if (ret != 0)
				{
					std::cerr << "Error initializing pthread rwlock!" << std::endl;
				}
				assert(ret == 0);

				this->recursed = 0;
			}

			~BK_Tree()
			{
				this->clear_tree();
			}

			int clear_tree(void)
			{
				int cleared = 0;
				// std::cout << "Destroying BK_Tree instance" << std::endl;
				if (this->tree != NULL)
				{
					cleared += this->tree->clear_node();
					delete this->tree;

					// Now I'm just being silly.
					this->tree = NULL;
				}
				return cleared;

			}

			/**
			 * @brief Insert an hash-data pair into the BK tree with proper write-locking.
			 *
			 * @param nodeHash hash to insert
			 * @param nodeData data associated with the hash value.
			 */
			void insert(hash_type nodeHash, data_type nodeData)
			{
				this->get_write_lock();
				if (this->tree == NULL)
					this->tree = new BK_Tree_Node(nodeHash, nodeData);
				else
					this->tree->insert(nodeHash, nodeData);
				this->free_write_lock();
			}

			/**
			 * @brief Insert an hash-data pair into the BK tree without taking out
			 *        a write lock. POTENTIALLY DANGEROUS. This is only intended to be
			 *        used for high-speed initial population of the tree, where the user
			 *        manages the locking a higher-level (via `get_write_lock()`).
			 *
			 *
			 * @param nodeHash hash to insert
			 * @param nodeData data associated with the hash value.
			 */
			void unlocked_insert(hash_type nodeHash, data_type nodeData)
			{
				if (this->tree == NULL)
					this->tree = new BK_Tree_Node(nodeHash, nodeData);
				else
					this->tree->insert(nodeHash, nodeData);
			}


			/**
			 * @brief Fetch all data values within a specified hamming distance
			 *        of the specified hash.
			 *
			 * @param baseHash hash value for the distance benchmark.
			 * @param distance hamming distance to search within.
			 *
			 * @return std::pair<std::set<int64_t>, <int64_t>, where
			 *         the first item is a set of data-values for
			 *         hashes within the specified distance, and
			 *         the second is the number of tree nodes touched
			 *         during the search (for diagnostic purposes).
			 */
			search_ret unlocked_getWithinDistance(hash_type baseHash, int distance)
			{
				// std::cout << "Get within distance!" << std::endl;

				if (this->tree == NULL)
				{
					search_ret ret = {{}, 0};
					return ret;
				}
				else
				{
					auto ret = this->tree->search(baseHash, distance);
					return ret;
				}
			}


			/**
			 * @brief Given the hash and data-value for a item,
			 *        find and remove it from the tree.
			 * @details Removes an item from the tree by hash and
			 *          id. This may involve reconstructing up to
			 *          the entire tree, in a worst-case circumstance.
			 *
			 *          If the specified hash<->data pair is not found,
			 *          nothing will be done, and no error will be raised.
			 *
			 * @param nodeHash hash to remove
			 * @param nodeData id to remove
			 *
			 * @return std::vector<int64_t> containing 2 status values.
			 *         The first is a count of the number of children
			 *         that were actually deleted by the remove call (which
			 *         should really only ever be 1).
			 *         The second is the number of child-nodes that had to be re-inserted to
			 *         accomodate any deletion of any nodes.
			 */
			std::vector<int64_t> remove(hash_type nodeHash, data_type nodeData)
			{
				this->get_write_lock();
				if (this->tree == NULL)
				{
					std::vector<int64_t> ret = {0, 0};
					this->free_read_lock();
					return ret;
				}
				auto rm_status = this->tree->remove(nodeHash, nodeData);

				// bool rebuild = rm_status[0]; // Rebuilding is handled in tree.remove()
				int deleted  = rm_status[1];
				int moved    = rm_status[2];

				this->free_write_lock();
				std::vector<int64_t> ret(2);
				ret[0] = deleted;
				ret[1] = moved;
				return ret;
			}

			/**
			 * @brief Fetch all data values within a specified hamming distance
			 *        of the specified hash.
			 *
			 * @param baseHash hash value for the distance benchmark.
			 * @param distance hamming distance to search within.
			 *
			 * @return std::pair<std::set<int64_t>, <int64_t>, where
			 *         the first item is a set of data-values for
			 *         hashes within the specified distance, and
			 *         the second is the number of tree nodes touched
			 *         during the search (for diagnostic purposes).
			 */
			search_ret getWithinDistance(hash_type baseHash, int distance)
			{
				// std::cout << "Get within distance!" << std::endl;
				this->get_read_lock();

				if (this->tree == NULL)
				{
					search_ret ret = {{}, 0};
					this->free_read_lock();
					return ret;
				}
				else
				{
					auto ret = this->tree->search(baseHash, distance);
					this->free_read_lock();
					return ret;
				}
			}

			/**
			 * @brief Get all items in the tree. Mostly for testing.
			 * @return std::deque<std::pair<hash_type, int64_t> > containing every
			 *         hash<->data pair in the entire tree.
			 *         Largely useful for unit testing, and probably not much else.
			 */
			return_deque get_all(void)
			{
				return_deque ret;
				this->get_read_lock();

				if (this->tree != NULL)
				{
					this->tree->get_contains(ret);
				}

				this->free_read_lock();
				return ret;
			}

			/**
			 * @brief Proxy calls to the lock mechanisms, exposed
			 *        so higher-level interfaces can do high-speed operations where they manage their
			 *        own locks.
			 */

			void get_read_lock(void)
			{
				// std::cout << "Read-lock acquisition!" << std::endl;
				pthread_rwlock_rdlock(&(this->lock_rw));
			}
			void get_write_lock(void)
			{
				pthread_rwlock_wrlock(&(this->lock_rw));
				// std::cout << "Write-lock acquisition -> " << this->recursed << "." << std::endl;
				if (this->recursed > 0)
				{
					throw std::runtime_error("Reentrant lock acquisition!");
				}
				this->recursed += 1;
			}

			void free_read_lock(void)
			{
				// std::cout << "Read-lock free!" << std::endl;
				pthread_rwlock_unlock(&(this->lock_rw));
			}
			void free_write_lock(void)
			{
				this->recursed -= 1;
				// std::cout << "Write-lock free -> " << this->recursed << "." << std::endl;
				pthread_rwlock_unlock(&(this->lock_rw));
			}


	};



}