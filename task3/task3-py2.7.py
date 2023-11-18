import os
import json
from fmm import Network, NetworkGraph, UBODTGenAlgorithm, UBODT, FastMapMatch, FastMapMatchConfig, STMATCH, STMATCHConfig

### Read network data
network = Network("../data/map/edges.shp", "fid", "u", "v")
print("Nodes {} edges {}".format(network.get_node_count(), network.get_edge_count()))
graph = NetworkGraph(network)

### Precompute an UBODT table
# Can be skipped if you already generated an ubodt file
if os.path.isfile("../data/map/ubodt.txt"):
    ubodt = UBODT.read_ubodt_csv("../data/map/ubodt.txt")
    print("Read the ubodt file")

### Read UBODT
else:
    print("Generate and read the ubodt file")
    ubodt_gen = UBODTGenAlgorithm(network, graph)
    status = ubodt_gen.generate_ubodt("../data/map/ubodt.txt", 0.03, binary=False, use_omp=True)
    print(status)
    ubodt = UBODT.read_ubodt_csv("../data/map/ubodt.txt")

### Create FMM model
fmm_model = FastMapMatch(network, graph, ubodt)

### Define map matching configurations
k = 16
radius = 0.005
gps_error = 0.0005
fmm_config = FastMapMatchConfig(k, radius, gps_error)

### Create STMATCH model
stmatch_model = STMATCH(network, graph)

### Define map matching configurations
k = 16
radius = 0.05
gps_error = 0.005
vmax = 0.003
factor = 1.5
stmatch_config = STMATCHConfig(k, radius, gps_error, vmax, factor)

### Read trajectory data
with open("../data/trajectory/train-1500.json", "r") as jsonfile:
    train1500 = json.load(jsonfile)

### Run map matching for wkt
for i, trajectory in enumerate(train1500):
    polyline = trajectory["POLYLINE"]
    wkt = "LINESTRING("+",".join([" ".join([str(k) for k in j]) for j in polyline])+")"
    result = fmm_model.match_wkt(wkt, fmm_config)
    train1500[i]["MAP_MATCHING_ALGORITHM"] = "fmm"

    if not list(result.cpath):
        result = stmatch_model.match_wkt(wkt, stmatch_config)
        train1500[i]["MAP_MATCHING_ALGORITHM"] = "stmatch"
        if not list(result.cpath):
            print(i, wkt)

    train1500[i]["MATCHED_RESULTS"] = {
        "Matched_path": list(result.cpath),
        "Matched_edge_for_each_point": list(result.opath),
        "Matched_edge_index": list(result.indices),
        "Matched_geometry": [[float(b) for b in a.split(" ")] for a in result.mgeom.export_wkt()[11:-1].split(",")] if len(result.mgeom.export_wkt()) > 12 else [],
        "Matched_point": [[float(b) for b in a.split(" ")] for a in result.pgeom.export_wkt()[11:-1].split(",")] if len(result.pgeom.export_wkt()) > 12 else [],
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
    print(i)

with open("../data/matched-results-1500.json", "w") as outfile:
    json.dump(train1500, outfile, indent=4)
