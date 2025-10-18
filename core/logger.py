<!,
                "level": "INFO",
                "propagate": True,
            },
        }
    })

    structlog.configure(
        processors=,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
]]>
