import argparse
from antibody_insight.desktop import launch

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Antibody Insight")
    parser.add_argument("project", nargs="?", help="Local .ais project")
    launch(parser.parse_args().project)
