import requests
import pandas as pd

# Download weather files
locations=pd.read_csv('Locations.csv',index_col=0)
output = r""
# base_url = r"https://power.larc.nasa.gov/api/temporal/hourly/point?time-standard=LST&parameters=WS10M,WD10M&community=RE&longitude={longitude}&latitude={latitude}&start={year}0101&end={year}1231&format=SAM"
base_url = r"https://power.larc.nasa.gov/api/temporal/hourly/point?time-standard=LST&parameters=WS10M,WD10M&community=RE&longitude={longitude}&latitude={latitude}&start={year}0101&end={year}1231&format=EPW"
weather_dir = "Weather files"
years=range(2001,2024)
# read in the locations file
# df = df.iloc[1:]
N_locations = len(locations)
 
# loop through the table, downloading the weather file if it doesn't exist
for index in locations.index:
    # read installation, and replace spaces with underscore in installation, removing leading and trailing spaces
    lat = locations.loc[index,'Lat']
    long = locations.loc[index,'Long']
    # print(f"Install = {installation} at Lat = [ {lat}, Long = {long}]")
    for year in years:
        fname = Path(".") / weather_dir / f"{lat}_{long}_{year}.epw"
        # if fname.exists():
        #     print(f'File {fname} already exists')
        # else:
        print(f"Downloading file {fname}")
        api_request_url = base_url.format(longitude=long, latitude=lat,year=year)
        response = requests.get(url=api_request_url, verify=True, timeout=30.00)
        if response.status_code != 200:
            print("Error in API request")
            print(f"Response Status Code = {response.status_code} ")
        else:
            print("Received Request")
            print(response.headers['content-disposition'])
            content = "\n".join(response.text.splitlines())
            print(f"Saving to file {fname}")
            with open(fname, 'w') as file_object:
                file_object.write(content)