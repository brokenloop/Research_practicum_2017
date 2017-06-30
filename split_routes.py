import pandas as pd
import os
import time

def get_line(string):
    if len(string) > 4:
        var = string[:4]
        var = var.lstrip("0")
        return var
    else:
        print("Error!")
        return None

def get_journey(string):
    if len(string) > 4:
        var = string[-4:]
        return var
    else:
        print("Error!")
        return None

def add_runtime(row, mydict):
    # Takes a row and a dictionary of start times
    # returns time elapsed (seconds) between that row's timestamp and the start of the line
    start = mydict[row.TimeFrame, row.VehicleJourneyID]["time"]
    current = row.Timestamp
    return (current - start) // 1000000


def insert_into_file(df, writefile):
    """  This function writes a dataframe (df) to a file (writefile),
        creating that file if it doesn't exist.
    """
    try:
        with open(writefile, 'a') as f:
            df.to_csv(f, header=False, index=False)
    except IOError:
        with open(writefile, 'w+') as f:
            df.to_csv(f, header=False, index=False)


def filter(filename, target_dir):

    print("Starting", filename)

    df = pd.read_csv(filename, low_memory=False, header=None)
    df.columns = ["Timestamp", "LineID", "Direction", "JourneyPatternID", "TimeFrame",
                  "VehicleJourneyID", "Operator", "Congestion", "Lon", "Lat",
                  "Delay", "BlockID", "VehicleID", "StopID", "AtStop"]

    # Select all columns of type 'object'
    object_columns = df.select_dtypes(['object']).columns

    # Convert selected columns to type 'category'
    for column in object_columns:
        df[column] = df[column].astype('category')

    # Convert other features to categorical
    for column in ['Congestion', 'BlockID', 'VehicleID', 'AtStop']:
        df[column] = df[column].astype('category')

    # Convert LineID & VehicleJourneyID features to str
    for column in ['LineID', 'VehicleJourneyID', ]:
        df[column] = df[column].astype('str')

    # Add column for human readable time
    df['HumanTime'] = pd.to_datetime(df['Timestamp'], unit='us')


    # Add day of week column
    df['Day'] = df['HumanTime'].dt.dayofweek

    # Add hour of day column
    df['Hour'] = df['HumanTime'].dt.hour


    # Dropping irrelevant columns
    for column in ['BlockID', 'Direction', 'Operator', 'Delay', 'Congestion']:
        df = df.drop(column, 1)


    df['LineID'] = df['JourneyPatternID'].apply(lambda x: get_line(x))
    df['JourneyPatternID'] = df['JourneyPatternID'].apply(lambda x: get_journey(x))

    # drop duplicate rows
    df = df.drop_duplicates(["TimeFrame", "VehicleJourneyID", "StopID"])

    # drop rows where bus isn't at stop
    df = df[(df.AtStop == 1)]

    # filter out routes which only have 1 stop.
    # This solves the problem of busses starting on the wrong side...
    df = df.groupby(['TimeFrame', 'VehicleJourneyID']).filter(lambda x: len(x) >= 3)

    # Putting the first sightings of a vehiclejourneyid and timeframe combo timestamp into a dictionary
    start_times = {}

    # This gives you the first line anything has been seen by
    firstlines = df.groupby(["TimeFrame", "VehicleJourneyID"]).head(1)

    # This iterates through them and assigns values to the dictionary
    for index, row in firstlines.iterrows():
        start_times[row.TimeFrame, row.VehicleJourneyID] = {"time":row.Timestamp, "loc":[row.Lat, row.Lon]}


    df['Runtime'] = ""

    # Applies this function to the newdf
    df['Runtime'] = df.apply(lambda row: add_runtime(row, start_times),axis=1)

    lines = df.LineID.unique()
    patterns = df.JourneyPatternID.unique()

    for line in lines:
        try:
            print("Writing line", line)
            line_df = df[df.LineID == line]
            insert_into_file(line_df, target_dir + line + ".csv")
        except:
            pass


def main(read_directory, write_directory):
    for read_file in os.listdir(read_directory):
        if read_file.endswith(".csv"):
            print("Reading", read_file, "from", read_directory)
            read_file = read_directory + "/" + read_file
            filter(read_file, write_directory)
            print("Finished", read_file)
            print()
    print("Finished main!")


if __name__=="__main__":
    start = time.time()

    read_directory1 = "bus_data/Dcc"
    read_directory2 = "bus_data/Sir"
    write_directory = "bus_data/line_data/"

    main(read_directory1, write_directory)
    main(read_directory2, write_directory)

    end = time.time()

    print()
    print("Program took", end - start, "seconds")