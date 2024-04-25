import streamlit as st
import requests
import pandas as pd
from PIL import Image
import spotipy
from spotipy import SpotifyOAuth
from spotipy.client import SpotifyException
import webbrowser
import io
from io import BytesIO
import base64

def set_default_cover():
    if artist_image_url != "":
        return get_image_from_url(artist_image_url)
    else:
        return "default-playlist-cover.png"


def get_image_from_url(image_url):
    try:
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            image_bytes = BytesIO(image_response.content)
            return Image.open(image_bytes)
        else:
            return False
    except Exception as e:
        return False

spotify_key = "4deea18e81a04f68b25d4368813b0134"
spotify_secret = "2d0e76be78b54422b2d9fae7c71f1ff9"
spotify_base_url = 'https://api.spotify.com/v1/'
redirect_uri = 'http://localhost:8501/'
auth_url = "https://accounts.spotify.com/api/token"
auth_response = requests.post(auth_url, {
    'grant_type': 'client_credentials',
    'client_id': spotify_key,
    'client_secret': spotify_secret,
})
auth_data = auth_response.json()
access_token = auth_data['access_token']
headers = {
    'Authorization': 'Bearer {token}'.format(token=access_token)
}
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=spotify_key,
    client_secret=spotify_secret,
    redirect_uri=redirect_uri,
    scope='playlist-modify-public playlist-modify-private ugc-image-upload'
))
auth_url = sp.auth_manager.get_authorize_url()

st.header("Playlist Creator")
st.subheader(":rainbow[Create a playlist to help you prep for an upcoming concert!]")
st.write("**If you plan to add your playlist to Spotify, "
         "click here and continue on the new tab.**")

st.sidebar.header("Concert Prep")
st.sidebar.page_link("main.py", label="Home", icon="🎧")
st.sidebar.page_link("pages/playlist_creator.py", label="Playlist Creator", icon="🎤")
st.sidebar.page_link("pages/concert_info.py", label="Concert Info", icon="🎸")
st.sidebar.page_link("pages/vibe_checker.py", label="Vibe Checker", icon="🎶")

login = st.button("Log in to Spotify")
if login:
    webbrowser.open_new_tab(auth_url)
auth_code = ""
if "auth_code" in st.session_state:
    auth_code = st.session_state.auth_code
    sp.auth_manager.get_access_token(auth_code)
if auth_code != "":
    st.success("Successfully logged in! You may now close the other tab.")
else:
    st.warning("You are currently not logged in.")

st.divider()

form = st.form("artist_search")
artist_input = form.text_input("**Search for an Artist**", placeholder="Enter artist name")
search = form.form_submit_button(label='Search')

if artist_input != "":
    # search for artist based on text input (name), limited to 10 results
    search_response = requests.get(
        spotify_base_url + 'search?q={artist_name}&type=artist&limit=10'.format(artist_name=artist_input),
        headers=headers)
    search_dict = search_response.json()

    artist_results = []
    artist_dict_indices = []
    for i in range(len(search_dict.get("artists").get("items"))):
        # exclude artists with no top songs (only check low popularity to decrease number of API calls)
        if search_dict["artists"]["items"][i]["popularity"] <= 25:
            id = search_dict["artists"]["items"][i]["id"]
            t_response = requests.get(spotify_base_url + 'artists/{id}/top-tracks'.format(id=id),
                                      headers=headers)
            t_dict = t_response.json()

            if len(t_dict["tracks"]) > 2:
                artist_results.append(search_dict["artists"]["items"][i]["name"])
                artist_dict_indices.append(i)
        else:
            artist_results.append(search_dict["artists"]["items"][i]["name"])
            artist_dict_indices.append(i)

    # format func allows us to save index of the option that is chosen instead of the option label (makes more sense in this case)
    artist_index = st.selectbox("**Select Artist**", range(len(artist_results)),
                                format_func=lambda x: artist_results[x], index=None, key=1)

    if artist_index != None:
        artist_name = artist_results[artist_index]
        artist_index = artist_dict_indices[artist_index]
        artist_id = search_dict["artists"]["items"][artist_index]["id"]

        tracks_response = requests.get(spotify_base_url + 'artists/{id}/top-tracks'.format(id=artist_id),
                                       headers=headers)
        tracks_dict = tracks_response.json()

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader(artist_name)

            artist_uri = search_dict["artists"]["items"][artist_index]["uri"]

            genres = set()
            for i in range(len(search_dict["artists"]["items"][artist_index]["genres"])):
                genres.add(search_dict["artists"]["items"][artist_index]["genres"][i])

            if len(genres) > 0:
                genres_str = ", ".join(genres)
            else:
                genres_str = "N/A"

            st.write("**Genres:** " + genres_str)

            popularity = search_dict["artists"]["items"][artist_index]["popularity"]
            st.write("**Popularity Rating:** " + str(popularity) + "%")

            no_tracks = False
            if (len(tracks_dict["tracks"]) > 0):
                top_song_name = tracks_dict["tracks"][0]["name"]
                st.write("**Top Song:** \"" + top_song_name + "\"")
            else:
                st.write("**Top Song:** N/A")
                no_tracks = True

            found_preview = False
            for i in range(len(tracks_dict["tracks"])):
                if tracks_dict["tracks"][i]["preview_url"]:
                    st.write("**Song Preview:** " + "\"" + tracks_dict["tracks"][i]["name"] + "\"")
                    st.audio(tracks_dict["tracks"][i]["preview_url"])
                    found_preview = True
                    break
            if not found_preview:
                st.write("**Song Preview:** N/A")

            if st.button(":rainbow[**Vibe Check This Artist!**]"):
                st.session_state.artist_name = artist_name
                st.session_state.artist_id = artist_id
                st.switch_page("pages/vibe_checker.py")

        with col2:
            if (len(search_dict["artists"]["items"][artist_index]["images"]) > 0):
                artist_image_url = search_dict["artists"]["items"][artist_index]["images"][0]["url"]
            else:
                artist_image_url = "https://t4.ftcdn.net/jpg/00/64/67/63/360_F_64676383_LdbmhiNM6Ypzb3FM4PPuFP9rHe7ri8Ju.jpg"
            st.image(artist_image_url)

        st.divider()

        playlist_name = st.text_input("**Playlist Name**", placeholder="Name your concert playlist")
        if not playlist_name.strip():
            playlist_name = artist_name + " Concert Prep Playlist"

        cover_type = st.selectbox("**Playlist Cover Image Type**",
                                  options=["Default", "URL", "Upload Image", "Solid Color"])

        col3, col4 = st.columns(2)
        with col4:
            playlist_cover = set_default_cover()
            image_type = "Default"
            if cover_type != "":
                if cover_type == "Default":
                    playlist_cover = set_default_cover()
                if cover_type == "URL":
                    # testing url: https://picsum.photos/200/300
                    cover_url = st.text_input("**Cover URL**", placeholder="Enter the URL of the cover image")
                    if cover_url != "":
                        image = get_image_from_url(cover_url)
                        if not image:
                            st.error("Invalid image url.")
                        else:
                            st.success("Successfully extracted playlist cover image!")
                            playlist_cover = image
                            image_type = "URL"
                if cover_type == "Upload Image":
                    uploaded_image = st.file_uploader("**Choose an image**")
                    if uploaded_image:
                        file_extension = uploaded_image.name.split('.')[-1].lower()
                        if file_extension not in ['jpg', 'jpeg']:
                            st.error("Invalid image format. Please upload a JPG image.")
                            image_type = "Default"
                        else:
                            st.success("Successfully uploaded playlist cover image!")
                            uploaded_image_bytes = BytesIO(uploaded_image.read())
                            playlist_cover = Image.open(uploaded_image_bytes)
                            image_type = "Uploaded Image"
                if cover_type == "Solid Color":
                    color = st.color_picker("**Color Picker**", value="#43B3FF")
                    playlist_cover = Image.new("RGB", (200, 200), color)
                    image_type = "Solid Color"
        with col3:
            st.write("\n")
            if playlist_cover and playlist_cover != "":
                width, height = playlist_cover.size
                size = min(width, height)
                left = int((width - size) / 2)
                upper = int((height - size) / 2)
                right = int(left + size)
                lower = int(upper + size)
                cropped_cover = playlist_cover.crop((left, upper, right, lower))

                # image to be used for playlist
                playlist_cover = cropped_cover.resize((500, 500))

                # preview smaller temp image in order to maintain quality of original image
                cover_preview = playlist_cover.resize((200, 200))
                st.image(cover_preview, caption="Current Cover: " + image_type)

        playlist_description = st.text_area("**Playlist Description**",
                                            placeholder="Add an optional description for your playlist")
        st.divider()

        num_songs = st.number_input("**Playlist Song Count (max. 50 songs)**", value=20, min_value=10, max_value=50,
                                    placeholder="Enter the number of songs to be added to your playlist")

        st.write("\n")
        st.write("**Top Albums to Include in Playlist:**")
        albums = {}
        # since we can't fetch every album's top songs, only include albums that have a top track for that artist
        for i in range(len(tracks_dict["tracks"])):
            album = tracks_dict["tracks"][i]["album"]["name"]
            album_id = tracks_dict["tracks"][i]["album"]["id"]
            if album_id not in albums:
                # dict keys: album ID, dict values: if an album is selected or not
                albums[album_id] = st.checkbox("\"" + album + "\"", value=True)

        selected_albums = [album for album, selected in albums.items() if selected]

        album_ids = ""
        for album in selected_albums:
            album_ids += album + ','

        album_ids = album_ids[:len(album_ids) - 1]

        # get more songs from selected albums to populate playlist (will return in order of decreasing popularity)
        albums_response = requests.get(spotify_base_url + 'albums?ids={ids}'.format(ids=album_ids),
                                       headers=headers)
        albums_dict = albums_response.json()

        if "albums" not in albums_dict:
            st.error("Selected artist has no albums.")
        else:
            # convert duration (ms) to minutes and seconds for tracks
            for i, track in enumerate(tracks_dict['tracks']):
                tracks_dict['tracks'][i]['duration_ms'] = pd.to_datetime(tracks_dict['tracks'][i]['duration_ms'],
                                                                         unit='ms').strftime('%M:%S')
            for i, album in enumerate(albums_dict['albums']):
                for j, track in enumerate(albums_dict['albums'][i]['tracks']['items']):
                    albums_dict['albums'][i]['tracks']['items'][j]['duration_ms'] = pd.to_datetime(
                        albums_dict['albums'][i]['tracks']['items'][j]['duration_ms'], unit='ms').strftime('%M:%S')

            tracks_data = []
            track_ids = set()
            # add data from top 10 songs from top albums to be the minimum 10
            for track in tracks_dict['tracks']:
                track_data = {
                    'Track Name': track['name'],
                    'Album Name': track['album']['name'],
                    'Release Date': track['album']['release_date'],
                    'Duration': track['duration_ms'],
                    'Track URI': track['uri']
                }
                tracks_data.append(track_data)
                track_ids.add(track["id"])

            other_tracks_data = []
            # add data from other songs from top albums (up to max songs defined by user)
            for i, album in enumerate(albums_dict['albums']):
                for track in albums_dict['albums'][i]['tracks']['items']:
                    track_data = {
                        'Track Name': track['name'],
                        'Album Name': album['name'],
                        'Release Date': album['release_date'],
                        'Duration': track['duration_ms'],
                        'Track URI': track['uri']
                    }
                    if track["id"] not in track_ids:
                        other_tracks_data.append(track_data)
                        track_ids.add(track["id"])

            # create dataframe for playlist preview table
            df_tracks = pd.DataFrame(tracks_data)
            df_other_tracks = pd.DataFrame(other_tracks_data)

            # randomize order so there is a mix of selected albums
            df_other_tracks = df_other_tracks.sample(frac=1.0, random_state=42)

            df_tracks = pd.concat([df_tracks, df_other_tracks])

            if len(df_tracks) < num_songs:
                st.warning("Unable to create a playlist with {num_songs} songs due to selected album filters.".format(
                    num_songs=num_songs))
                num_songs = len(df_tracks)

            st.divider()

            col5, col6 = st.columns([2, 1])
            with col5:
                st.header("**Playlist Preview**")
                if playlist_name != "":
                    st.subheader(playlist_name)
                else:
                    st.subheader("**Name:** N/A")
                if playlist_description != "":
                    st.write("**Description:** " + playlist_description)
                else:
                    st.write("**Description:** N/A")

            with col6:
                st.image(cover_preview)

            st.write("\n")

            # display DataFrame as a table with indices starting from 1
            df_tracks.reset_index(drop=True, inplace=True)
            df_tracks.index += 1
            st.dataframe(df_tracks.head(num_songs), use_container_width=True)

            # Iterate over the DataFrame rows and get the track URIs
            track_uris = []
            empty_playlist = False
            if len(df_tracks) == 0:
                st.error("Your playlist is empty! Please update your selected album filters.".format(num_songs=num_songs))
                empty_playlist = True
            else:
                for i, row in df_tracks.iterrows():
                    track_uri = row['Track URI']
                    track_uris.append(track_uri)
                    if i - 1 == num_songs - 1:
                        break

            st.divider()

            # adding playlist to the user's spotify account logic
            if auth_code != "" and not empty_playlist:
                st.subheader("Add to Spotify")
                username_form = st.form("username")
                username = username_form.text_input("**Spotify Username**", placeholder="Enter your username to continue.")
                add_playlist = username_form.form_submit_button(label='Add Playlist')
                if username != "":
                    if add_playlist:
                        try:
                            img_byte_arr = io.BytesIO()
                            playlist_cover.save(img_byte_arr, format='JPEG')
                            img_byte_arr = img_byte_arr.getvalue()
                            encoded_img = base64.b64encode(img_byte_arr).decode()

                            playlist = sp.user_playlist_create(username, playlist_name, description=playlist_description)
                            sp.playlist_add_items(playlist['id'], track_uris)
                            sp.playlist_upload_cover_image(playlist['id'], encoded_img)
                            st.success(f'Playlist "{playlist_name}" successfully created and added to your Spotify!')
                        except SpotifyException as se:
                            error_message = se.msg
                            if "cannot create a playlist for another user" in error_message:
                                st.error("Could not add playlist. Make sure your username is correct.")
                            elif "not registered in the Developer Dashboard" in error_message:
                                st.info("Could not add playlist. Our app is currently in development, so users must be "
                                        "registered on our Spotify Developer Dashboard in order to use the app as intended.")
                            elif "Max Retries" in error_message:
                                st.error("Rate limit reached. Please wait a while before trying again.")
                            else:
                                st.error(error_message)
                        except Exception as e:
                            st.warning("Something went wrong.")
                            st.write(e)