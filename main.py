def create_parser():
# Parse arguments
    parser = argparse.ArgumentParser(description='A handelsregister CLI')
    parser.add_argument(
                          "-d",
                          "--debug",
                          help="Enable debug mode and activate logging",
                          action="store_true"
                        )
    parser.add_argument(
                          "-f",
                          "--force",
                          help="Force a fresh pull and skip the cache",
                          action="store_true"
                        )
    parser.add_argument(
                          "-s",
                          "--schlagwoerter",
                          help="Search for the provided keywords",
                          required=False,
                          default=""
                        )
    parser.add_argument(
                          "-so",
                          "--schlagwortOptionen",
                          help="Keyword options: all=contain all keywords; min=contain at least one keyword; exact=contain the exact company name.",
                          choices=["all", "min", "exact"],
                          required= True,
                          default="all"
                        )
    parser.add_argument(
                          "-ra",
                          "--registerArt",
                          help="Registerart options: alle, HRA, HRB, GnR, PR, VR.",
                          choices=["HRA", "HRB", "GnR", "PR", "VR"],
                          default=""
                        )
    parser.add_argument(  #form:registerNummer
                          "-rn",
                          "--registerNummer",
                          help="Register number, without the type",
                          default=""
                        )
    parser.add_argument(  #form:registergericht or form:registergericht_focus -> rather form:registergericht_input
                          "-rc",
                          "--registerCourt",
                          help="Register court of the company",
                          default=""
                        )
    parser.add_argument(
                          "-dtd",
                          "--documentsToDownload",
                          help="AD = Aktueller Abdruck, CD = Chronologischer Abdruck, SI = Strukturiertes Inhalt",
                          choices=["AD", "CD", "SI"],
                          default=""
                        )



    return parser

if __name__ == "__main__":
    parser = create_parser()