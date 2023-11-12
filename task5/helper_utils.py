from dataclasses import dataclass
from geopandas import GeoDataFrame
import numpy as np
from typing import Iterable
from datetime import datetime, timedelta
import networkx as nx
import pandas as pd

def swap_col(x:np.ndarray):
    x[:,[0,1]] = x[:,[1,0]]
    return x

@dataclass
class Segments:
    states: list[tuple[int,int]]
    df: GeoDataFrame | pd.DataFrame
    
    @staticmethod
    def from_state(states:list[tuple[int,int]],nodes_proj:GeoDataFrame):
        states = states
        df = nodes_proj.loc[[s[0] for s in states]]
        return Segments(states,df)
    
@dataclass
class MatchedRoutes:

    matched_path : np.ndarray
    matched_edge: np.ndarray
    gps_coords : np.ndarray
    gps_time: Iterable[datetime]
    matched_geo: np.ndarray
    matched_geo_time: Iterable[datetime]
    matched_point: np.ndarray
    osmid_source: np.ndarray
    osmid_target: np.ndarray
    matched_info: list[dict]
    taxi_id: str
    trip_id: str
    call_type: str
    # graph: nx.Graph
    
    @staticmethod
    def get_graph(osm_source:list[str],
                  source_lnglat:np.ndarray,
                  osm_target:list[str],
                  target_lnglat:np.ndarray,)->nx.Graph:

        #Remove duplicates but keep order
        # osm_source = list(dict.fromkeys(osm_source))  
        # osm_target = list(dict.fromkeys(osm_target))
        
        G=nx.Graph()
        for source,s_pos,target,t_pos in zip(osm_source,
                                             source_lnglat,
                                             osm_target,
                                             target_lnglat):
            G.add_node(source,pos=s_pos)
            # G.add_node(target,pos=t_pos)
            # G.add_edge(source, target)
            # nx.get_node_attributes(G,'pos')
        for nodeA,nodeB in zip(osm_source[:-1],osm_source[1:]):
            G.add_edge(nodeA, nodeB)
            
        return G
    
    @staticmethod
    def get_time_array(df:pd.Series,n:int,dt:None|timedelta=None)->Iterable[datetime]:
        gps_time = [datetime.fromtimestamp(df['TIMESTAMP'])]
        for _ in range(n):
            if dt:
                gps_time.append(dt) # type: ignore
            else:
                gps_time.append(timedelta(seconds=15)) # type: ignore
        return np.cumsum(gps_time) # type: ignore
    
    @staticmethod
    def from_df(df:pd.Series,nodes_proj:pd.DataFrame):
        gps_coords = swap_col(np.asarray(df['POLYLINE']).reshape(-1,2))
        gps_time = MatchedRoutes.get_time_array(df,n=gps_coords.shape[0])
        
        matched_edge = df['MATCHED_RESULTS']['Matched_edge_for_each_point']
        matched_path = df['MATCHED_RESULTS']['Matched_path']
        matched_info = df['MATCHED_RESULTS']['Detailed_match_infromation']
        matched_point = swap_col(np.asarray(df['MATCHED_RESULTS']['Matched_point']).reshape(-1,2)) #lat,lon
        matched_geo = swap_col(np.asarray(df['MATCHED_RESULTS']['Matched_geometry']).reshape(-1,2)) #lat,lon
        
        dt = (gps_time[-1]-gps_time[0])/matched_geo.shape[0] # type: ignore
        geo_time =  MatchedRoutes.get_time_array(df,n=matched_geo.shape[0],dt=dt)
        
        osmid_source = np.asarray([x['source'] for x in matched_info])
        osmid_target = np.asarray([x['target'] for x in matched_info])

        taxi_id = df['TAXI_ID']
        trip_id = df['TRIP_ID']
        call_type = df['CALL_TYPE']
        # graph = MatchedRoutes.get_graph(osmid_source,
        #                                 nodes_proj.loc[osmid_source][['lon','lat']].values,
        #                                 osmid_target,
        #                                 nodes_proj.loc[osmid_target][['lon','lat']].values)
        
        return MatchedRoutes(matched_path,matched_edge,
                             gps_coords,gps_time,
                             matched_geo,geo_time,
                             matched_point,osmid_source,
                             osmid_target,matched_info,
                             taxi_id,trip_id,call_type)#,graph)
    