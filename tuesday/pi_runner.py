from sensor import SensorHub

if __name__ == "__main__":
    hub = SensorHub(sample_period=2.0)

    # Optional first calibration (run once in clean air)
    # hub.do_calibrate(seconds=60)

    print("Starting sensor loop (Pi) -> sending data to cloud...")
    hub.loop()