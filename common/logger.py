import logging
import config

default_conf = {"name": "unknown",
                "filename": config.LOG_PATH + "unknown.log",
                "format": "%(asctime)s: %(levelname)s %(funcName)s(), line %(lineno)d, %(message)s",
                "datefmt": "%H:%M:%S %m-%d",
                "level": config.LOG_LEVEL}

def get_logger_object(*args, **kwargs):
    d = dict(default_conf, **kwargs)
    logger = logging.getLogger(d["name"])
    hdlr = logging.FileHandler(d["filename"])
    print d['filename']
    formatter = logging.Formatter(d["format"], d["datefmt"])
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(d["level"])
    return logger

def main():
    log = get_logger_object()
    log.debug("test")
    print dir(log)

    print logging.NOTSET
    print logging.DEBUG
    print logging.INFO
    print logging.ERROR
    print logging.CRITICAL
    
if __name__ == '__main__':
    main()
