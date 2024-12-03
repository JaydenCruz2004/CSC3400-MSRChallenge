from py2neo import Graph

# Initialize connection to Neo4j
try:
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "password1"))
    print("Connected to Neo4j successfully.")
except Exception as e:
    print(f"Connection failed: {e}")
    graph = None

# Exit if connection fails
if graph is None:
    print("Cannot proceed: Neo4j connection is unavailable.")
    exit()

# Queries to analyze vulnerabilities
try:
    # Query 1: Find all vulnerable releases
    vulnerable_releases = graph.run("""
        MATCH (r:Release)-[:addedValues]->(v:AddedValue)
        WHERE v.type = 'CVE'
        RETURN r.id AS release, v.value AS cve
    """).data()
    print("Vulnerable Releases:")
    for vuln in vulnerable_releases:
        print(f"Release: {vuln['release']}, CVE: {vuln['cve']}")

    # Query 2: Propagate vulnerabilities
    for vuln in vulnerable_releases:
        release_id = vuln["release"]
        propagation = graph.run("""
            MATCH (vuln:Release {id: $release_id})-[:dependency*1..]->(affected:Release)
            RETURN affected.id AS affected_release
        """, release_id=release_id).data()
        print(f"\nPropagation for {release_id}:")
        for affected in propagation:
            print(f"Affected Release: {affected['affected_release']}")

    # Query 3: Most affected projects
    most_affected = graph.run("""
        MATCH (vuln:Release)-[:dependency*1..]->(affected:Release)
        WITH affected, COUNT(*) AS propagation_count
        ORDER BY propagation_count DESC
        RETURN affected.id AS project, propagation_count
        LIMIT 10
    """).data()
    print("\nMost Affected Projects:")
    for project in most_affected:
        print(f"Project: {project['project']}, Affected Count: {project['propagation_count']}")
except Exception as e:
    print(f"Error during analysis: {e}")
