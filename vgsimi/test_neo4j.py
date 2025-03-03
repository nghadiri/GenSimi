from neo4j import GraphDatabase
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Load settings (using your existing config setup)
from util.config import load_app_settings
settings = load_app_settings()
'''
uri = settings['neo4j']['uri']
user = settings['neo4j']['user']
password = settings['neo4j']['password']
'''
uri="bolt://10.33.70.51"
user="neo4j"
password="neo4j_new"


def test_connection():
    try:
        # Initialize the driver with encryption disabled
        driver = GraphDatabase.driver(
            uri, 
            auth=(user, password),
            encrypted=False  # Try without encryption first
        )
        
        # Verify connectivity
        driver.verify_connectivity()
        
        def create_test_node(tx):
            result = tx.run("""
                CREATE (n:TestNode {name: 'test'}) 
                RETURN n.name AS name
            """)
            return result.single()['name']
        
        with driver.session() as session:
            name = session.write_transaction(create_test_node)
            print(f"Created test node with name: {name}")
            
        driver.close()
        print("Connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during connection test: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Check if the Neo4j server is running:")
        print("   - Docker: docker ps | grep neo4j")
        print("2. Verify your connection URI:")
        print(f"   - Current URI: {uri}")
        print("   - Default local URI should be: 'bolt://localhost:7687'")
        print("3. Verify the port is correctly exposed if using Docker:")
        print("   - Check your docker-compose.yml or docker run command")
        print("4. Check if you can access Neo4j Browser:")
        print("   - Usually at http://localhost:7474")
        return False

if __name__ == "__main__":
    success = test_connection()
    if success:
        print("Neo4j connection is working properly")
    else:
        print("Failed to connect to Neo4j")