#include <iostream>
#include<iterator>
#include<filesystem>
#include<iostream>
#include<filesystem>
#include<fstream>
#include<regex>
#include<string>
#include<sstream>

int main()
{
	auto maybe_file{ std::filesystem::current_path() / "Data/rechtsform.txt" };

	std::ifstream file{maybe_file};

	std::ofstream worked_out{ std::filesystem::current_path() / "Data/rechtsform_fpy.txt"};
	//worked_out << "Nummer;Rechtsform\n";

	std::string helper;

	std::getline(file, helper, '.');

	
	while (std::getline(file, helper))
	{
		std::stringstream line(helper);
		while (std::getline(line, helper, ';'))
		{
			std::stringstream cell(helper);
			
			int number;
			cell >> number;
			
			char throw_away;
			cell >> throw_away;

			std::getline(cell, helper);
			
			worked_out << '\"' << helper << "\": " << number << ",\n";
		}
	}




	return 0;
}