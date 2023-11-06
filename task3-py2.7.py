import os
import json
from fmm import Network, NetworkGraph, UBODTGenAlgorithm, UBODT, FastMapMatch, FastMapMatchConfig, STMATCH, STMATCHConfig

### Read network data
place_name = "Porto, Portugal"
network = Network("./data/{place_name}/edges.shp".format(place_name = place_name), "fid", "u", "v")
print "Nodes {} edges {}".format(network.get_node_count(), network.get_edge_count())
graph = NetworkGraph(network)

### Precompute an UBODT table
# Can be skipped if you already generated an ubodt file
if os.path.isfile("./data/{place_name}/ubodt.txt".format(place_name = place_name)):
    ubodt = UBODT.read_ubodt_csv("./data/{place_name}/ubodt.txt".format(place_name = place_name))
    print 'Read the ubodt file'

### Read UBODT
else:
    print 'Generate and read the ubodt file'
    ubodt_gen = UBODTGenAlgorithm(network, graph)
    status = ubodt_gen.generate_ubodt("./data/{place_name}/ubodt.txt".format(place_name = place_name), 0.03, binary=False, use_omp=True)
    print status
    ubodt = UBODT.read_ubodt_csv("./data/{place_name}/ubodt.txt".format(place_name = place_name))

### Create FMM model
fmm_model = FastMapMatch(network, graph, ubodt)

### Define map matching configurations
k = 16
radius = 0.005
gps_error = 0.0005
fmm_config = FastMapMatchConfig(k, radius, gps_error)

### Read trajectory data
with open("./data/trajectory/train-1500.json", "r") as jsonfile:
    train1500 = json.load(jsonfile)

train50 = train1500[:50]

### Run map matching for wkt
for i, trajectory in enumerate(train50):
    polyline = trajectory['POLYLINE']
    wkt = 'LINESTRING('+','.join([' '.join([str(k) for k in j]) for j in polyline])+')'
    result = fmm_model.match_wkt(wkt, fmm_config)
    try:
        train50[i]["MATCHED_RESULTS"] = {
            "Matched_path": list(result.cpath),
            "Matched_edge_for_each_point": list(result.opath),
            "Matched_edge_index": list(result.indices),
            "Matched_geometry": result.mgeom.export_wkt(),
            "Matched_point": result.pgeom.export_wkt(),
            "Detailed_match_infromation": [
                {
                    "eid": c.edge_id,
                    "source": c.source,
                    "target": c.target,
                    "error": c.error,
                    "length": c.length,
                    "offset": c.offset,
                    "spdist": c.spdist,
                    "ep": c.ep,
                    "tp": c.tp,
                } for c in result.candidates
            ]
        }
    except:
        train50[i]["MATCHED_RESULTS"] = {}
    print(i)

with open("./data/matched-50-results.json", "w") as outfile:
    json.dump(train50, outfile, indent=4)
