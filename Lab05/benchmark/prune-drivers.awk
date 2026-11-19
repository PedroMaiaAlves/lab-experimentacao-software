BEGIN { in_dependency = 0; block = "" }

/<dependency>/ {
    in_dependency = 1
    block = $0 ORS
    next
}

in_dependency {
    block = block $0 ORS
    if (/<\/dependency>/) {
        if (block !~ /<artifactId>driver-(artemis|bookkeeper|jms|pulsar|kop|mqtt5|nats|nsq|pravega|redis|rocketmq|rocketmq5|nats-streaming)<\/artifactId>/) {
            printf "%s", block
        }
        in_dependency = 0
        block = ""
    }
    next
}

{ print }
