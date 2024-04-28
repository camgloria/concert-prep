import streamlit as st
import requests
import pandas as pd
import folium
from datetime import datetime

tm_key = "noF5kg6nwwXGlQ4UCnwm9YHGB8ADCjSt"

us_states = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    "District of Columbia": "DC",
    "Puerto Rico": "PR"
}

@st.cache_data
def generate_list_of_events_by_areacode_and_artist(state_code, attractionID):
    events_nearby_list_url = f"https://app.ticketmaster.com/discovery/v2/events.json?size=30&attractionId={attractionID}&stateCode={state_code}&apikey={tm_key}"
    events_nearby_list_dict = requests.get(events_nearby_list_url).json()
    return events_nearby_list_dict

@st.cache_data
def get_list_of_artists(artist):
    artist_list_url = f"https://app.ticketmaster.com/discovery/v2/attractions.json?classificationName=Music&keyword={artist}&apikey={tm_key}"
    artist_list_dict = requests.get(artist_list_url).json()
    return artist_list_dict


def create_map_with_markers(venue_coords, venue_names):
    m = folium.Map(location=[venue_coords[0]['latitude'], venue_coords[0]['longitude']], zoom_start=6, )

    for i, venue_coord in enumerate(venue_coords):
        #popup = folium.Popup(venue_names[i], parse_html=True)
        folium.Marker([venue_coord['latitude'], venue_coord['longitude']], tooltip=venue_names[i]).add_to(m)

    return m


def format_date(date_str):
    date = datetime.strptime(date_str, "%Y-%m-%d")
    formatted_date = date.strftime("%B %d, %Y").lstrip("0").replace(" 0", " ")
    return formatted_date


def get_artist_id_from_url(url):
    start_index = url.find("/artist/") + len("/artist/")
    end_index = url.find("?", start_index)
    artist_id = url[start_index:end_index]
    return artist_id


def get_max_resolution_image(images):
    max_resolution = 0
    max_resolution_url = -1

    for i, image_info in enumerate(images):
        resolution = image_info.get('width') * image_info.get('height')
        if resolution > max_resolution:
            max_resolution = resolution
            max_resolution_url = image_info.get('url')

    return max_resolution_url


st.sidebar.header("Concert Prep")
st.sidebar.page_link("main.py", label="Home", icon="🎧")
st.sidebar.page_link("pages/playlist_creator.py", label="Playlist Creator", icon="🎤")
st.sidebar.page_link("pages/concert_info.py", label="Concert Info", icon="🎸")
st.sidebar.page_link("pages/vibe_checker.py", label="Vibe Checker", icon="🎶")

st.header("Concert Info")
st.subheader(":rainbow[Get ticket and location info for concerts in your state!]")
st.write("\n")

form = st.form("concert_artist_search")
artist = form.text_input("**Search for an Artist**", placeholder="Enter artist name")
search = form.form_submit_button(label='Search')

if artist != "":
    artist_search_dict = get_list_of_artists(artist)

    if artist_search_dict["page"]["totalElements"] == 0:
        st.warning("No artists found.")
    else:
        artist_search_list = [i["name"] for i in artist_search_dict.get("_embedded", {}).get("attractions", [])]
        index = 0

        if len(artist_search_list) >= 2:
            st.info("Multiple artists found for \"" + artist + "\". Please select the closest match below:")
            artist_name = st.selectbox("**Select Artist**", options=artist_search_list, index=None)
            if artist_name:
                index = int(artist_search_list.index(artist_name))
        else:
            artist_name = artist_search_list[0]
            index = int(artist_search_list.index(artist_name))

        if artist_name:
            attractionID = artist_search_dict.get("_embedded").get("attractions")[index].get("id")

            st.write("\n")

            price_range = st.slider("**Ideal ticket price range (USD)**",
                                    min_value=0, max_value=1000, step=10,
                                    value=(50, 500))
            price_min = price_range[0]
            price_max = price_range[1]

            state_name = st.selectbox("**State**", us_states, index=None)
            state_code = ""
            if state_name:
                state_code = us_states[state_name]

            if state_code != "":
                events_nearby_list_dict = generate_list_of_events_by_areacode_and_artist(state_code, attractionID)
                venue_coords = []
                venue_names = []
                results = {}

                if events_nearby_list_dict["page"]["totalElements"] == 0:
                    st.warning("No upcoming concerts found for selected state.")

                else:
                    for i in range(events_nearby_list_dict.get("page").get("totalElements")):
                        event_name = events_nearby_list_dict.get("_embedded").get("events")[i].get("name") + " in " + \
                                     events_nearby_list_dict.get("_embedded").get("events")[i].get("_embedded").get("venues")[
                                  0].get("city").get("name") + ", " + \
                                     events_nearby_list_dict.get("_embedded").get("events")[i].get("_embedded").get("venues")[
                                  0].get("state").get("name") + " on " + \
                                     events_nearby_list_dict.get("_embedded").get("events")[i].get("dates").get("start").get(
                                  "localDate")
                        event_url = events_nearby_list_dict.get("_embedded").get("events")[i].get("url")

                        if events_nearby_list_dict.get("_embedded").get("events")[i].get("priceRanges") is None or \
                                events_nearby_list_dict.get("_embedded").get("events")[i].get("priceRanges")[0] is None:
                            ticket_min = ticket_max = -1
                            min_high = max_high = min_low = max_low = 0

                        else:
                            if events_nearby_list_dict.get("_embedded").get("events")[i].get("priceRanges")[0].get(
                                    "min") is None:
                                ticket_min = -1
                                st.warning("No minimum price found")

                            else:
                                ticket_min = events_nearby_list_dict.get("_embedded").get("events")[i].get("priceRanges")[
                                    0].get("min")

                            if events_nearby_list_dict.get("_embedded").get("events")[i].get("priceRanges")[0].get(
                                    "max") is None or \
                                    events_nearby_list_dict.get("_embedded").get("events")[i].get("priceRanges")[
                                        0] is None or events_nearby_list_dict.get("_embedded").get("events")[i].get(
                                "priceRanges") is None:
                                ticket_max = -1
                                st.warning("No maximum price found")

                            else:
                                ticket_max = events_nearby_list_dict.get("_embedded").get("events")[i].get("priceRanges")[
                                    0].get("max")

                            if ticket_min and ticket_max:
                                min_dif = ticket_min - price_min
                                max_dif = ticket_max - price_max

                                if min_dif > 0:
                                    min_high = ticket_min
                                    min_low = 0
                                else:
                                    min_low = ticket_min
                                    min_high = 0
                                if max_dif > 0:
                                    max_high = ticket_max
                                    max_low = 0
                                else:
                                    max_low = ticket_max
                                    max_high = 0

                        results[i] = {
                            'Event Name': event_name,
                            'URL': event_url,
                            'Minimum Price': ticket_min,
                            'Maximum Price': ticket_max,
                            'Maximum Price Too High': max_high,
                            'Maximum Price Low': max_low,
                            'Minimum Price Too High': min_high,
                            'Minimum Price Low': min_low
                        }

                    chart_data = pd.DataFrame.from_dict(results, orient='index')

                    event_names = set()
                    for event in events_nearby_list_dict.get("_embedded").get("events"):
                        event_names.add(event["name"])
                    if len(event_names) == 1:
                        event_name = list(event_names)[0]
                    else:
                        event_name = artist + " Events"

                    event_dates = []
                    for event in events_nearby_list_dict.get("_embedded").get("events"):
                        event_dates.append(event.get("dates").get("start").get("localDate"))
                    event_dates = sorted(event_dates)

                    for i, event in enumerate(event_dates):
                        event_dates[i] = format_date(event)

                    st.write("\n")
                    tab1, tab2, tab3 = st.tabs(["Concert Info", "Ticket Prices", "Venues"])

                    with tab1:
                        st.subheader(event_name)
                        col1, col2 = st.columns(2)

                        with col1:
                            num_events = len(events_nearby_list_dict.get("_embedded").get("events"))

                            if num_events > 1:
                                st.write("**{artist_name} is performing at {num} upcoming events in {state}!**".format(artist_name=artist_name, num=num_events,
                                                                                                    state=state_name))
                                st.write("**Date Range:** " + event_dates[0] + " - " + event_dates[-1])
                            else:
                                st.write("**{artist_name} is performing at {num} upcoming event in {state}!**".format(artist_name=artist_name, num=num_events,
                                                                                                    state=state_name))
                                st.write("**Date:** " + event_dates[0])

                            genre = events_nearby_list_dict.get("_embedded").get("events")[0].get("classifications")[0].get("genre").get("name").lower()
                            subgenre = events_nearby_list_dict.get("_embedded").get("events")[0].get("classifications")[0].get("subGenre").get("name").lower()
                            if subgenre != genre:
                                st.write("**Genres:** " + genre + ", " + subgenre)
                            elif genre != "undefined":
                                st.write("**Genres:** " + genre)
                            else:
                                st.write("**Genres:** N/A")

                            if len(artist_search_dict.get("_embedded").get("attractions")[int(artist_search_list.index(artist_name))].get("externalLinks").get("spotify")) > 0:
                                #get artist id from here to be used in playlist creator/vibe checker
                                spotify_link = artist_search_dict.get("_embedded").get("attractions")[int(artist_search_list.index(artist_name))].get("externalLinks").get("spotify")[0].get("url")
                                st.write("**Spotify ID:** " + get_artist_id_from_url(spotify_link))

                            event_link = f"https://ticketmaster.com/{artist}-tickets/artist/{attractionID}".format(artist=artist, attractionID=attractionID)
                            st.link_button("Get Tickets!", event_link)

                        with col2:
                            if len(events_nearby_list_dict.get("_embedded").get("events")[0].get("images")) > 0:
                                concert_image = get_max_resolution_image(events_nearby_list_dict.get("_embedded").get("events")[0].get("images"))
                                st.image(concert_image)

                    with tab2:
                        st.subheader("Ticket Prices in " + state_name)
                        st.write("**{name}**".format(name=event_name))

                        st.write("\n")
                        if events_nearby_list_dict.get("_embedded").get("events")[0].get("priceRanges"):
                            min_price = events_nearby_list_dict.get("_embedded").get("events")[0].get("priceRanges")[0].get("min")
                            max_price = events_nearby_list_dict.get("_embedded").get("events")[0].get("priceRanges")[0].get("max")
                            st.write("**Ticket Price Range:** \${:.2f} - \${:.2f}".format(min_price, max_price))
                            st.write("\n")

                            help = st.toggle("Explain what I'm looking at")
                            if help:
                                st.info("The chart below displays concerts ticket prices in your state.\n"
                                        "\nIf you see :orange[ORANGE], your minimum price is NOT enough to buy the minimum price tickets at that concert.\n"
                                        "\nIf you see :blue[BLUE], your minimum price IS enough to buy the minimum price tickets at that concert!\n"
                                        "\nIf you see :green[GREEN], your maximum price IS enough to buy the maximum price tickets at that concert!\n"
                                        "\nIf you see :red[RED], your maximum price is NOT enough to buy the maximum price tickets at that concert.")

                            st.bar_chart(
                                chart_data, x="Event Name", y=["Maximum Price Too High", "Maximum Price Low", "Minimum Price Too High", "Minimum Price Low"],
                                color=["#1B9500", "#870101", "#1982d8", "#ff9113"], width=800, height=500)
                        else:
                            st.warning("No ticket price information is available.")

                    with tab3:
                        for event in events_nearby_list_dict.get("_embedded", {}).get("events", []):
                            venues = event.get("_embedded", {}).get("venues", [])
                            for venue in venues:
                                lng = float(venue["location"]["longitude"])
                                lat = float(venue["location"]["latitude"])
                                venue_coords.append({'latitude': lat, 'longitude': lng})
                                venue_names.append(venue['name'])

                        st.subheader("Concert Locations in " + state_name)
                        st.write("**{name}**".format(name=event_name))
                        st.components.v1.html(create_map_with_markers(venue_coords, venue_names)._repr_html_(), width=700,
                                                height=600)

                        #seatmap = events_nearby_list_dict.get("_embedded").get("events")[0].get("seatmap").get("staticUrl")
                        #st.image(seatmap)