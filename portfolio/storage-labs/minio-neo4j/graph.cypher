// New minimal scenario based on the report's graph-storage task.
// MERGE makes repeat execution idempotent; does not delete existing graph data.
MERGE (system:PortfolioSystem {name:'Training IAS'})
MERGE (db:PortfolioAsset {name:'Project database'})
MERGE (threat:PortfolioThreat {name:'Unauthorized reading'})
MERGE (measure:PortfolioMeasure {name:'Role separation'})
MERGE (system)-[:CONTAINS]->(db)
MERGE (threat)-[:AFFECTS]->(db)
MERGE (measure)-[:MITIGATES]->(threat);

MATCH (measure:PortfolioMeasure)-[:MITIGATES]->(threat)-[:AFFECTS]->(asset)
RETURN measure.name,threat.name,asset.name;
