"""
SeisDown is a lightweight and user-friendly software designed to facilitate the download of seismic data. 
To use SeisDown, please read the readme tutorial.

Author : Thibaut Céci (thi.ceci@gmail.com)
"""

import os
import re

from obspy import UTCDateTime
from obspy.clients.fdsn import Client
from obspy.geodetics import locations2degrees
import pandas as pd
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tqdm import tqdm


## List of clients for downloading seismic data
clients_list = {
    # "AUSPASS": Client("AUSPASS"),
    # "BGR": Client("BGR"),
    # "EIDA": Client("EIDA"),
    "EMSC": Client("EMSC"),
    # "ETH": Client("ETH"),
    # "GEOFON": Client("GEOFON"),
    "GEONET": Client("GEONET"),
    # "GFZ": Client("GFZ"),
    # "ICGC": Client("ICGC"),
    "INGV": Client("INGV"),
    "IPGP": Client("IPGP"),
    "IRIS": Client("IRIS"),
    "IRISPH5": Client("IRISPH5"),
    # "ISC": Client("ISC"),
    # "KNMI": Client("KNMI"),
    # "KOERI": Client("KOERI"),
    # "LMU": Client("LMU"),
    # "NCEDC": Client("NCEDC"),
    # "NIEP": Client("NIEP"),
    # "NOA": Client("NOA"),
    # "ODC": Client("ODC"),
    # "ORFEUS": Client("ORFEUS"),
    # "RASPISHAKE": Client("RASPISHAKE"),
    "RESIF": Client("RESIF"),
    "RESIFPH5": Client("RESIFPH5"),
    # "SCEDC": Client("SCEDC"),
    # "TEXNET": Client("TEXNET"),
    # "UIB-NORSAR": Client("UIB-NORSAR"),
    "USGS": Client("USGS")
    # "USP": Client("USP")
}

selected_client = clients_list["IRIS"]


def download_inventory(event, starttime_user, latitude_user, longitude_user, time_margins, maxradius, retries=10):
    """
    Downloads the station inventory for a given seismic event.
    
    Parameters:
    -----------
    event : Event
        Seismic event object containing attributes like latitude, longitude, starttime and endtime.
    starttime_user : str
        The name of the column where the start time of events in the catalog is located.
    latitude_user : str
        The name of the column where the latitude of events in the catalog is located.
    longitude_user : str
        The name of the column where the longitude of events in the catalog is located.
    time_margins : float
        The number of seconds to add to the start and end times of the event.    
    maxradius : float
        Maximum radius around the event's location to search for stations (in deg).
    retries : int
        Number of retry attempts in case of failure.
        
    Returns:
    --------
    Inventory
        Inventory object
    """

    ## Start time and end time of the event
    start = UTCDateTime(event[starttime_user.get()])
    start, end = start - time_margins.get(), start + (time_margins.get() * 2)

    ## Download station inventory from client
    for attempt in range(retries):
        try:
            return selected_client.get_stations(
                latitude=event[latitude_user.get()],
                longitude=event[longitude_user.get()],
                startbefore=start,
                endafter=end,
                maxradius=maxradius,
                channel="BH*,HH*,EH*,EH*,HN*"
            )
        
        ## If an error occurs, the code restarts
        except Exception as e:
            print(f"Error during inventory download. Attempt {attempt + 1} of {retries}. Error: {e}")
    return []


def download_stream(event, starttime_user, latitude_user, longitude_user, time_margins, retries=3, output_dir="sismogrammes"):
    """
    Download the waveforms for a given event.

    Parameters
    ----------
    event : pd.Series
        A series containing the event information.
    starttime_user : str
        The name of the column where the start time of events in the catalog is located.
    latitude_user : str
        The name of the column where the latitude of events in the catalog is located.
    longitude_user : str
        The name of the column where the longitude of events in the catalog is located.
    time_margins : float
        The number of seconds to add to the start and end times of the event.
    retries : int
        Number of times to retry the request in case of an error.
    output_dir : str
        The folder where the data will be saved.
    """

    ## Start time and end time of the event
    start = UTCDateTime(event[starttime_user.get()])
    start, end = start - time_margins.get(), start + (time_margins.get() * 2)

    ## Loop through each seismic network
    for network in tqdm(event.inventory):
        for station in network:
            for attempt in range(retries):
                try:
                    ## Request data
                    traces = selected_client.get_waveforms(network.code, station.code, "*", "BH*,HH*,EH*,EH*,HN*", start, end, attach_response=True)
                    traces.merge(method=1, fill_value="interpolate")
                    distance = locations2degrees(event[latitude_user.get()], event[longitude_user.get()], station.latitude, station.longitude)

                    ## Save each trace to a SAC format
                    for trace in traces:
                        trace.stats.distance = distance * 111.19

                        output_path = os.path.join(output_dir, f"{trace.stats.station}_{trace.stats.channel}.sac")
                        trace.write(output_path, format="SAC")
                    break

                except Exception as e:
                    print(f"Error with station {station}. Attempt {attempt + 1} of {retries}. Error: {e}")
                    continue


def download_event(event, index):
    """
    Create a folder to save the waveforms for a given event after downloading.

    Parameters
    ----------
    event : pd.Series
        A series containing the event information.
    index : int
        The index of the event.
    """

    # try:
    ## Download the inventory of the event
    inventory = download_inventory(event, starttime_user, latitude_user, longitude_user, time_margin_user, maxradius_user.get(), retries=3)
    event["inventory"] = inventory

    ## Create a folder for the event
    event_date = event.get(starttime_user.get(), "UnknownDate")
    event_magnitude = event.get(magnitude_user.get(), "UnknownMagnitude")
    event_location = event.get(place_user.get(), "UnknownLocation")
    premier_mot = event_location.split()[0]

    try:
        try:
            deuxieme_mot = event_location.split()[1]
            troisieme = event_location.split()[2]
            mot = premier_mot + "_" + deuxieme_mot + "_" + troisieme
            event_date = ''.join(re.findall(r'\d', event_date))
            folder_name = os.path.join(os.getcwd(), f"{event_date}_M{event_magnitude}_{mot}")

        except:
            deuxieme_mot = event_location.split()[1]
            mot = premier_mot + "_" + deuxieme_mot
            event_date = ''.join(re.findall(r'\d', event_date))
            folder_name = os.path.join(os.getcwd(), f"{event_date}_M{event_magnitude}_{mot}")

    except:
        event_date = ''.join(re.findall(r'\d', event_date))
        folder_name = os.path.join(os.getcwd(), f"{event_date}_M{event_magnitude}_{premier_mot}")

    os.makedirs(folder_name, exist_ok=True)

    ## Download the seismic data of the event and save in the new folder
    download_stream(event, starttime_user, latitude_user, longitude_user, time_margin_user, retries=1, output_dir=folder_name)

    messagebox.showinfo("Download complete", f"The event {index} was successfully downloaded.")

    # except Exception as e:
    #     messagebox.showerror("Error", f"An error occurred while downloading the event {index}: {e}")


def open_catalog():
    """
    Open a seismic event catalog.
    Only .txt or .csv format are supported.
    """

    ## Open the catalog of the user
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("CSV Files", "*.csv")])
    
    ## Check if a file was selected
    if file_path:
        global catalog
        
        ## Read the catalog
        catalog = pd.read_csv(file_path, sep=sep_user.get())
        
        ## Display the contents of the catalog
        display_catalog()


def display_catalog():
    """
    Display the catalog in a new window.
    """

    ## Create a new window to display the catalog
    new_window = tk.Toplevel(root)
    new_window.title("Catalog")
    frame = tk.Frame(new_window)
    frame.pack(fill=tk.BOTH, expand=True)

    ## Add a column "Index" in the catalog
    columns = ["Index"] + list(catalog.columns)
    tree = ttk.Treeview(frame, columns=columns, show="headings")
    tree.heading("Index", text="Index")
    tree.column("Index", anchor="center")

    ## Setting columns
    for col in catalog.columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center")

    tree.pack(fill=tk.BOTH, expand=True)

    for index, row in catalog.iterrows():
        tree.insert("", tk.END, values=[index] + list(row))


    def click():
        """
        Action when a user clicks on the download button.
        """

        def notify_start():
            messagebox.showinfo("Downloading in progress, please wait!", 
                                "Downloading in progress, please wait! A new window will open when the download is finished. "
                                "If a new window opens and no data has been downloaded, you may need to change clients.")

        def notify_error():
            messagebox.showerror("Error", "Index out of range.")

        def notify_invalid_index():
            messagebox.showerror("Error", "Please enter a valid index.")

        try:
            root.after(0, notify_start)

            selected_index = int(line_input.get())

            if 0 <= selected_index < len(catalog):
                thread = threading.Thread(target=download_event, args=(catalog.iloc[selected_index], selected_index))
                thread.start()
            else:
                root.after(0, notify_error)

        except ValueError:
            root.after(0, notify_invalid_index)


    ## Setting the new window
    tk.Label(new_window, text="Download an event (by its index):").pack()
    line_input = tk.Entry(new_window)
    line_input.pack()
    tk.Button(new_window, text="Download", command=click).pack()
    

def change_client(event):
    """
    Change the client based on the user's choice.
    """

    global selected_client
    
    ## Retrieve the selected client
    selected_client = clients_list[client_user.get()]


#####################
### The main code ###
#####################

root = tk.Tk()
root.title("SeisDown Interface")

guide_text = """
Welcome to the SeisDown software interface !
This short tutorial will guide you through the steps to use the software :

1. Start by choosing the separator (Separator) then you will be able to click on the "Import a catalog" button to import the catalog. The file must be in .txt or .csv format.
2. Specify the columns containing essential information such as the event's start time, magnitude and the area where the event occurred.
3. Define the maximum search radius for seismic stations (Maxradius) and indicate the time margins duration for downloading seismic data (Timemargins).
4. Select the seismic data client to use.
5. Choose the index of the event to download.
6. Click the "Download Data" button to start downloading the seismic data for the event, then wait for the download complete message to appear.

If the client has no data, go back to step 4 and choose another client.

------------------------------------------------------------------------------------------------------------------------------------------------------

Bienvenue dans l'interface du logiciel SeisDown !
Ce petit tutoriel va vous guider à travers les étapes pour utiliser le logiciel :

1. Commencer par choisir le séparateur (Separator) pour ensuite pouvoir cliquer sur le bouton "Import a catalog" pour importer le catalogue de données. Le fichier doit être au format .txt ou .csv.
2. Spécifiez les colonnes contenant les informations essentielles telles que le temps de début de l'événement, la magnitude et la zone ou l'événement a eu lieu.
3. Définissez le rayon maximal de recherche des stations sismiques (Maxradius) et indiquer la durée des marges de temps pour télécharger les données sismiques (Timemargins).
4. Sélectionnez le client de données sismiques à utiliser.
5. Choisissez l'index de l'événement à télécharger.
6. Cliquez sur le bouton "Download Data" pour lancer le téléchargement des données sismiques de l'événement, puis attendez l'apparition du message de fin de téléchargement.

Si le client ne possède pas de données, repartir de l'étape 4 et choisir un autre client.
"""

interface = tk.Text(root, wrap=tk.WORD, height=18, width=150)
interface.insert(tk.END, guide_text)
interface.config(state=tk.DISABLED)
interface.pack(padx=10, pady=10)

main = tk.Frame(root)
main.pack(padx=10, pady=10)

## Add buttons
button = tk.Button(main, text="Import a catalog", command=open_catalog)
button.grid(row=1, column=0, padx=10, pady=5)

tk.Label(main, text="Maxradius :").grid(row=2, column=0)
maxradius_user = tk.DoubleVar(value=5.0)
tk.Entry(main, textvariable=maxradius_user).grid(row=2, column=1)

tk.Label(main, text="Time margins :").grid(row=3, column=0)
time_margin_user = tk.IntVar(value=500)
tk.Entry(main, textvariable=time_margin_user).grid(row=3, column=1)

tk.Label(main, text="Column with start time :").grid(row=4, column=0)
starttime_user = tk.StringVar(value="starttime")
tk.Entry(main, textvariable=starttime_user).grid(row=4, column=1)

tk.Label(main, text="Column with magnitude :").grid(row=5, column=0)
magnitude_user = tk.StringVar(value="Mag")
tk.Entry(main, textvariable=magnitude_user).grid(row=5, column=1)

tk.Label(main, text="Column with area :").grid(row=6, column=0)
place_user = tk.StringVar(value="Région")
tk.Entry(main, textvariable=place_user).grid(row=6, column=1)

tk.Label(main, text="Column with latitude :").grid(row=7, column=0)
latitude_user = tk.StringVar(value="latitude")
tk.Entry(main, textvariable=latitude_user).grid(row=7, column=1)

tk.Label(main, text="Column with longitude :").grid(row=8, column=0)
longitude_user = tk.StringVar(value="longitude")
tk.Entry(main, textvariable=longitude_user).grid(row=8, column=1)

tk.Label(main, text="Separator").grid(row=0, column=0)
sep_user = tk.StringVar(value=",")
tk.Entry(main, textvariable=sep_user).grid(row=0, column=1)

tk.Label(main, text="Select a client :").grid(row=9, column=0)
client_user = ttk.Combobox(main, values=list(clients_list.keys()), state="readonly")
client_user.set("IRIS")
client_user.grid(row=9, column=1)
client_user.bind("<<ComboboxSelected>>", change_client)

root.mainloop()