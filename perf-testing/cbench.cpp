#include <stdio.h>
#include <stdint.h>
#include <iostream>
#include <random>
#include <hayai.hpp>
#include "../deduplicator/bktree.hpp"


#define TEST_TREE_SIZE 8000000

class BK_Tree_Fixture : public ::hayai::Fixture
{
public:

	BK_Tree_Ns::BK_Tree *tree;
	std::mt19937_64 generator;

	virtual void SetUp()
	{
		this->generator.seed(12345);
		std::cout << "Building " << TEST_TREE_SIZE << " node testing-tree..." << std::endl;
		this->tree = new BK_Tree_Ns::BK_Tree(0, 0);
		for (int x = 1; x < TEST_TREE_SIZE; x += 1)
		{
			this->tree->insert(this->generator(), x);
		}
		std::cout << "Tree built. Doing performance queries." << std::endl;
	}

	virtual void TearDown()
	{
		std::cout << "Deallocating tree." << std::endl;
		delete this->tree;
		std::cout << "Tree deallocated." << std::endl;
	}

	int Tree_Search()
	{
		this->tree->getWithinDistance(this->generator(), 4);
	}

};

BENCHMARK_F(BK_Tree_Fixture, Tree_Search, 2, 10000)
{
	Tree_Search();
}


int main()
{
	std::cout << "Doing benchmark" << std::endl;


	hayai::ConsoleOutputter consoleOutputter;

	hayai::Benchmarker::AddOutputter(consoleOutputter);
	hayai::Benchmarker::RunAllTests();



	std::cout << "Done" << std::endl;
	return 0;
}