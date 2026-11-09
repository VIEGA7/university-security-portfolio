// mongosh, after connecting to the local lab. The bundle must be imported first.
use('portfolio_lab');
db.mitre_attack.countDocuments({});
db.mitre_attack.find({type:'attack-pattern'}, {id:1,name:1}).limit(10);
db.mitre_attack.find({type:'attack-pattern', revoked:{$ne:true}, x_mitre_deprecated:{$ne:true}},
                    {id:1,name:1}).limit(10);
db.mitre_attack.aggregate([{$group:{_id:'$type',count:{$sum:1}}},{$sort:{count:-1}}]);
db.mitre_attack.find({'external_references.external_id':'T1055.011'}, {id:1,name:1});
