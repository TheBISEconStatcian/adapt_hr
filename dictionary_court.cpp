#include <iostream>
#include<iterator>
#include<filesystem>
#include<iomanip>
#include<iostream>
#include<filesystem>
#include<fstream>
#include<regex>
#include<string>
#include<sstream>

struct register_encode
{ 
	std::string code, name;
	std::string csv_str()
	{
		return name + ';' + code + '\n';
	}
	std::string json_str()
	{
		std::stringstream builder;
		builder << std::quoted(name) << ": " << std::quoted(code) << ",\n";
		return builder.str();
	}
};

register_encode extract_entry(std::stringstream& option)
{
	std::string a_help;

	register_encode output;

	//throw away first part until code
	std::getline(option, a_help, '\"');

	std::getline(option, output.code, '\"'); //retrieve code

	std::getline(option, a_help, '>'); //throw away until register

	std::getline(option, output.name, '<'); //get register name

	return output;
}

static std::regex option_pattern("<option(.*?)</option>");

std::stringstream extract_options(const std::string& line)
{
	std::stringstream output;

	for (std::sregex_iterator it_op(line.begin(), line.end(), option_pattern), no_more_matches;
		it_op != no_more_matches; ++it_op)
	{
		const std::smatch& option = *it_op;
		output << option.str() << '\n';
	}

	return output;
}

int main()
{
	auto to_mine{ std::filesystem::current_path() / "Data/register_to_mine.txt" };
	std::ifstream file{to_mine};

	auto mined_path{ std::filesystem::current_path() / "Data/register_code_py.txt" };
	std::ofstream mined{mined_path};

	auto csv_path{ std::filesystem::current_path() / "Data/register_code.csv" };
	std::ofstream csv_mined{csv_path};
	csv_mined << "Amtsgericht;Code\n";

	std::string line;
	while (std::getline(file, line))
	{
		std::stringstream options(extract_options(line));
		std::string option;
		while (std::getline(options, option))
		{
			std::stringstream ss_option(option);
			register_encode decoder(extract_entry(ss_option));
			mined << decoder.json_str();
			csv_mined << decoder.csv_str();
		}
	}

	return 0;
}