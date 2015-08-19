from firebase import firebase
import config

CONFIG_FILE_PATH = "/root/data/dash-board/docker/config.ini"


def main():
    appconfig = config.getConfiguration(CONFIG_FILE_PATH)
    if appconfig is None:
        message = "Error parsing config file"
        raise Exception(message)

    print appconfig
    required_config_keys = ['firebase']
    for key in required_config_keys:
        if key not in appconfig:
            message = "*** ERROR: key \'%s\' is required" % key
            raise Exception(message)

    dashstats_auth = firebase.FirebaseAuthentication(appconfig['firebase']['token'], appconfig['firebase']['email'])
    dashstats = firebase.FirebaseApplication(appconfig['firebase']['url'], dashstats_auth)
    #database clean up
    #we only need 1440 records to fill a 24h chart with 100 points/ chart resolution 14,4 minutes
    #will leave 1500 records and delete the rest. this increases board start
    records = dashstats.get("stats", None, {'shallow': 'true'})
    print records
    print "total records: %s" % len(records)
    nrecs = len(records) - 1500
    print "records to delete: %s" % nrecs
    if nrecs > 0:
        recs_to_delete = dashstats.get("stats", None, {'orderBy': '"timestamp"', 'limitToFirst': nrecs})
        for rec in recs_to_delete:
            print "deleting record %s:%s" % (rec, recs_to_delete[rec]['timestamp'])
            dashstats.delete("stats", rec)

if __name__ == "__main__":
    main()
