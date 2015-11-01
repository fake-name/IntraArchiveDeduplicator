#include <stdio.h>
#include <stdint.h>
#include <iostream>
#include <random>
#include <hayai.hpp>
#include "../deduplicator/bktree.hpp"


class HammingBenchFixture : public ::hayai::Fixture
{
public:

	int64_t x;
	int64_t y;

	virtual void SetUp()
	{
		std::mt19937_64 generator(12345);
		this->x = generator();
		this->y = generator();
	}

	virtual void TearDown()
	{

	}

	int Hamming()
	{
		BK_Tree_Ns::f_hamming(this->x, this->y);
	}

};

BENCHMARK_F(HammingBenchFixture, Hamming, 10000, 10)
{
	Hamming();
}


int main()
{
	std::cout << "Doing benchmark" << std::endl;


	 root(0, 0);



	hayai::ConsoleOutputter consoleOutputter;

	hayai::Benchmarker::AddOutputter(consoleOutputter);
	hayai::Benchmarker::RunAllTests();



	std::cout << "Done" << std::endl;
	return 0;
}