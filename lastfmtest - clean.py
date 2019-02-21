import requests
import networkx as nx 
import matplotlib.pyplot as plt
import time
from plotly.offline import download_plotlyjs, init_notebook_mode,  iplot, plot

class Artist:
	def __init__(self, name, listened, mbid=-1):
		self.name = name 
		self.mbid = mbid
		self.count = 1
		self.listened = listened
		self.neighbors = []

		
	def __iadd__(self, other):
		self.count += other
		return self
		
def build_map(prune):
	username = input("Username: ")
	
	length = input("What length of time do you want to search through? (overall | 7day | 1month | 3month | 6month | 12month): ")
	lengths = ["overall", "7day", "1month", "3month", "6month", "12month"]
	while(length not in lengths):
		length = input("I'm sorry, I didn't recognize that. The available options are: (overall | 7day | 1month | 3month | 6month | 12month). Please try again, "
		" or enter 'q' to give up: ")
		if(length == "q"):
			exit()

	depth = input("How many related artists do you want to search? ")
	limit = input("How many of your listened artists do you want to search through? ")
	
	api_key = "KEY"

	username_request = "http://ws.audioscrobbler.com/2.0/?method=user.gettopartists&user={}&limit={}&length={}&api_key={}&format=json".format(username, limit, length, api_key)

	response = requests.get(username_request)
	data = response.json()
	artist_list = data["topartists"]["artist"]
	map = {}

	for elem in artist_list:
		if elem["name"] in map:
			map[elem["name"]].listened = True
		else:
			try:
				map[elem["name"]] = Artist(elem["name"], True, elem["mbid"])
			except:
				map[elem["name"]] = Artist(elem["name"], True)

		# We can't do anything without an mbid
		try:
			mbid = elem["mbid"]
		except:
			continue
			
		time.sleep(0.25) # Don't make too many requests!
		similar_request = "http://ws.audioscrobbler.com/2.0/?method=artist.getsimilar&mbid=%s&api_key=%s&format=json&limit=%s" % (mbid, api_key, depth)
		similar_response = requests.get(similar_request)
		similar_data = similar_response.json()
		if "similarartists" not in similar_data:
			continue

		similar_artist_list = similar_data["similarartists"]["artist"]

		for artist in similar_artist_list:
				
			if not artist["name"] in map:
				if "mbid" in artist:
					map[artist["name"]] = Artist(artist["name"], False, artist["mbid"])
				else:
					map[artist["name"]] = Artist(artist["name"], False)
			else:
				map[artist["name"]] += 1

			map[elem["name"]].neighbors.append(map[artist["name"]])
			map[artist["name"]].neighbors.append(map[elem["name"]])

	if(prune):
		for key in list(map):
			if(not map[key].listened and len(map[key].neighbors) == 1):
				del map[key]
				
	return map
	
def build_graph(map, prune):
	G = nx.Graph()
	for key in map:
		G.add_node(map[key])
		
	for key in map:
		for neighbor in map[key].neighbors:
			if(prune):
				if(not neighbor.listened and len(neighbor.neighbors) > 1):
					G.add_edge(map[key], neighbor)
			else:
				G.add_edge(map[key], neighbor)
			
	if(prune):
		G.remove_nodes_from(list(nx.isolates(G)))
	return G
	
"""
Functions lightly altered from:
https://plot.ly/~empet/14683/networks-with-plotly/#/
"""


def show_graph_as_plotly(G):
	pos = nx.spring_layout(G)
	
	Xn=[pos[k][0] for k in pos.keys()]
	Yn=[pos[k][1] for k in pos.keys()]
	labels = []
	annotations_text = {}
	colors = []
	for node in G.nodes:
		labels.append(node.name)
		if(node.listened):
			colors.append('rgb(240,0,0)')
			annotations_text[node] = node.name
		else:
			colors.append('rgb(0,240,0)')
			annotations_text[node] = ""

	annotations = []
	for k in pos.keys():
		annotations.append(dict(text=annotations_text[k], 
                                x=pos[k][0], 
                                y=pos[k][1]+0.035,#this additional value is chosen by trial and error
                                xref='x1', yref='y1',
                                font=dict(color= "rgb(10,10,10)", size=14),
                                showarrow=False)
                          );
		
	trace_nodes=dict(type='scatter',
				 x=Xn, 
				 y=Yn,
				 mode='markers',
				 marker=dict(size=28, color=colors),
				 text=annotations,
				 textposition="bottom center",
				 hoverinfo='text',
				 hovertext=labels
)
				 
	Xe=[]
	Ye=[]
	for e in G.edges():
		Xe.extend([pos[e[0]][0], pos[e[1]][0], None])
		Ye.extend([pos[e[0]][1], pos[e[1]][1], None])

	trace_edges=dict(type='scatter',
					 mode='lines',
					 x=Xe,
					 y=Ye,
					 line=dict(width=1, color='rgb(25,25,25)'),
					 hoverinfo='none' 
					)
					
	axis=dict(showline=False, # hide axis line, grid, ticklabels and  title
			  zeroline=False,
			  showgrid=False,
			  showticklabels=False,
			  title='' 
			  )
	layout=dict(title= 'My Graph',	
				font= dict(family='Balto'),
				width=1500,
				height=1500,
				autosize=False,
				showlegend=False,
				xaxis=axis,
				yaxis=axis,
				margin=dict(
				l=40,
				r=40,
				b=85,
				t=100,
				pad=0,
		   
		),
		hovermode='closest',
		plot_bgcolor='#efecea', #set background color			 
		)


	fig = dict(data=[trace_edges, trace_nodes], layout=layout)
	fig['layout'].update(annotations=annotations)
	plot(fig)

def get_prune():
	prune = input("Prune unconnected related artists? (y/n): ")

	while(prune not in ["y", "n"]):
		prune = input("I'm sorry, I didn't recognize that. The available options are: (y/n), "
		" or enter 'q' to give up: ")
	if(prune == "q"):
		exit()
	
	if(prune == "y"):
		return True
	else:
		return False


prune = get_prune()
map = build_map(prune)
G = build_graph(map, prune)
pos = nx.spring_layout(G)
show_graph_as_plotly(G)
	
	
	
	

	
	
	
	
	
	
	
	
	
	
	
	
	
