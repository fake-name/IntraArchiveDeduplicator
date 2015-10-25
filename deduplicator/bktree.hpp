


#include <unordered_map>
#include <memory>
#include <utility>
#include <set>
#include <stdint.h>




namespace bk_tree
{
	typedef std::pair<set<int64_t>, int64_t> search_ret;

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

		uint64_t a = reinterpret_cast<uint64_t>(a_int);
		uint64_t b = reinterpret_cast<uint64_t>(b_int);

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
		int64_t                                                 node_hash;

		// Unordered set is slower for small
		// numbers of n, which we mostly have.
		std::set<int64_t>                                       node_ids;

		// We have to have a shared_ptr because
		// unordered_map cannot have members with incomplete types.
		std::unordered_map<int, std::shared_ptr<BK_Tree_Node> > children;

		BK_Tree_Node(int64_t nodeHash, int64_t node_id)
		{
			this->node_ids.insert(node_id);
			this->node_hash = node_hash;
		}

		void insert(int64_t nodeHash, int64_t nodeData)
		{

		}
		void remove(int64_t nodeHash, int64_t nodeData)
		{

		}
		search_ret getWithinDistance(int64_t baseHash, int distance)
		{

		}
	};
}