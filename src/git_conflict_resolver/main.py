from .crew import GitConflictResolverCrew
import os

os.makedirs('output', exist_ok=True)

def run():
    """
    Run the Resolver crew.
    """
    resolver_crew = GitConflictResolverCrew()
    inputs = {
        'directory': '',
    }

    # Create and run the crew
    result = resolver_crew().crew.kickoff(inputs=inputs)

    print(result.raw)

    print("\n\nReport has been saved to output/conflicts.md")


if __name__ == "__main__":
    run()