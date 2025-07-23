package io.devhands;

import org.apache.kafka.common.serialization.Serdes;

import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.KeyValue;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;

import org.apache.kafka.streams.kstream.Consumed;
import org.apache.kafka.streams.kstream.Produced;
import org.apache.kafka.streams.kstream.Grouped;
import org.apache.kafka.streams.kstream.Printed;

import org.apache.kafka.streams.kstream.KStream;
import org.apache.kafka.streams.kstream.KTable;
import org.apache.kafka.streams.kstream.GlobalKTable;
import org.apache.kafka.streams.kstream.Materialized;
import org.apache.kafka.streams.kstream.TimeWindows;
import org.apache.kafka.streams.kstream.SessionWindows;
import org.apache.kafka.streams.kstream.SlidingWindows;

import org.apache.kafka.common.utils.Bytes;
import org.apache.kafka.streams.state.KeyValueStore;
import org.apache.kafka.streams.state.Stores;


import java.io.FileInputStream;
import java.io.IOException;
import java.time.Duration;
import java.util.List;
import java.util.Properties;
import java.util.concurrent.CountDownLatch;

import org.apache.kafka.streams.kstream.Suppressed;

import static org.apache.kafka.streams.kstream.Suppressed.*;
import static org.apache.kafka.streams.kstream.Suppressed.BufferConfig.*;

import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;

public class StatefulStreams {
    private static DateTimeFormatter formatter = DateTimeFormatter.ofPattern("HH:mm:ss");

    private static String timeFormat(long timestamp) {
        return LocalDateTime.ofInstant(
                Instant.ofEpochMilli(timestamp),
                ZoneId.systemDefault()
        ).format(formatter);
    }

    public static void main(String[] args) throws IOException {
        Properties props = new Properties();
        try (FileInputStream fis = new FileInputStream("streams.properties")) {
            props.load(fis);
        }

        props.put("application.id", "stateful-app-1"); // group
        props.put("consumer.group.instance.id", "consumer-id-1");

        props.put("commit.interval.ms", "2500");
        props.put("state.dir", "data");

        final String sourceTopic = "user-events";
        final String outputTopic = "streams-agg-output";
        final String searchPrefix = "amount";

        StreamsBuilder builder = new StreamsBuilder();

        System.out.println("Consuming from topic [" + sourceTopic + "] and producing to [" + outputTopic + "]");

        KStream<String, String> sourceStream = builder.stream(sourceTopic,
                Consumed.with(Serdes.String(), Serdes.String()));

        sourceStream
                .filter((key, value) -> value.contains(searchPrefix))
                .peek((key, value) -> System.out.println("In  >> key: " + key + ":\t" + value))
                .mapValues(value -> {
                    // Extract the amount value from JSON
                    int amountStart = value.indexOf("\"amount\":") + 9; // 9 is length of "\"amount\":"
                    int amountEnd = value.indexOf(',', amountStart);
                    if (amountEnd == -1) amountEnd = value.indexOf('}', amountStart);
                    if (amountEnd == -1) amountEnd = value.length();
                    String amountStr = value.substring(amountStart, amountEnd).trim();
                    return Double.parseDouble(amountStr);
                })
                .groupByKey(Grouped.with(Serdes.String(), Serdes.Double()))
                .aggregate(
                        () -> 0.0, // Initializer
                        (key, value, aggregate) -> aggregate + value,
                        Materialized.with(Serdes.String(), Serdes.Double())
                )
                .toStream()
                .peek((key, value) -> System.out.println("Out << key: " + key + ":\t" + value))
                .to(outputTopic, Produced.with(Serdes.String(), Serdes.Double()));
        ;

        try (KafkaStreams kafkaStreams = new KafkaStreams(builder.build(), props)) {
            final CountDownLatch shutdownLatch = new CountDownLatch(1);
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                kafkaStreams.close(Duration.ofSeconds(1));
                shutdownLatch.countDown();
            }));
            try {
                kafkaStreams.start();
                shutdownLatch.await();
            } catch (Throwable e) {
                System.exit(1);
            }
        }
        System.exit(0);
    }
}
