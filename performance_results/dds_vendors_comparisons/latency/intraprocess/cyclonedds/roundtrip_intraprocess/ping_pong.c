#include "dds/dds.h"
#include "RoundTrip.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <inttypes.h>
#include <pthread.h>

#define TIME_STATS_SIZE_INCREMENT 50000
#define MAX_SAMPLES 100
#define US_IN_ONE_SEC 1000000LL

/* Forward declaration */
void *pub_main (void *args);
void *sub_main (void *args);
static dds_entity_t pub_prepare_dds(dds_entity_t *pub_writer, dds_entity_t *pub_reader, dds_entity_t *pub_read_cond, dds_listener_t *listener);
static void pub_finalize_dds(dds_entity_t pub_participant);
static dds_entity_t sub_prepare_dds(dds_entity_t *writer, dds_entity_t *reader, dds_entity_t *readCond, dds_listener_t *listener);
static void sub_finalize_dds(dds_entity_t participant, RoundTripModule_DataType data[MAX_SAMPLES]);

typedef struct
{
  uint32_t payloadSize;
  uint64_t numSamples;
  dds_time_t timeOut;
  bool use_listener;
} latency_args;

typedef struct ExampleTimeStats
{
  dds_time_t * values;
  unsigned long valuesSize;
  unsigned long valuesMax;
  double average;
  dds_time_t min;
  dds_time_t max;
  unsigned long count;
} ExampleTimeStats;

static void exampleInitTimeStats (ExampleTimeStats *stats)
{
  stats->values = (dds_time_t*) malloc (TIME_STATS_SIZE_INCREMENT * sizeof (dds_time_t));
  stats->valuesSize = 0;
  stats->valuesMax = TIME_STATS_SIZE_INCREMENT;
  stats->average = 0;
  stats->min = 0;
  stats->max = 0;
  stats->count = 0;
}

static void exampleResetTimeStats (ExampleTimeStats *stats)
{
  memset (stats->values, 0, stats->valuesMax * sizeof (dds_time_t));
  stats->valuesSize = 0;
  stats->average = 0;
  stats->min = 0;
  stats->max = 0;
  stats->count = 0;
}

static void exampleDeleteTimeStats (ExampleTimeStats *stats)
{
  free (stats->values);
}

static ExampleTimeStats *exampleAddTimingToTimeStats
  (ExampleTimeStats *stats, dds_time_t timing)
{
  if (stats->valuesSize > stats->valuesMax)
  {
    dds_time_t * temp = (dds_time_t*) realloc (stats->values, (stats->valuesMax + TIME_STATS_SIZE_INCREMENT) * sizeof (dds_time_t));
    stats->values = temp;
    stats->valuesMax += TIME_STATS_SIZE_INCREMENT;
  }
  if (stats->values != NULL && stats->valuesSize < stats->valuesMax)
  {
    stats->values[stats->valuesSize++] = timing;
  }
  stats->average = ((double)stats->count * stats->average + (double)timing) / (double)(stats->count + 1);
  stats->min = (stats->count == 0 || timing < stats->min) ? timing : stats->min;
  stats->max = (stats->count == 0 || timing > stats->max) ? timing : stats->max;
  stats->count++;

  return stats;
}

static void usage(void)
{
  printf ("Usage (parameters must be supplied in order):\n"
          "./ping [-l] [payloadSize (bytes, 0 - 100M)] [numSamples (0 = infinite)] [timeOut (seconds, 0 = infinite)] [outputCSV (filename)]\n"
          "./ping quit - ping sends a quit signal to pong.\n"
          "Defaults:\n"
          "./ping 0 0 0\n");
  exit(EXIT_FAILURE);
}

// Publisher
static dds_entity_t pub_writer;
static dds_entity_t pub_reader;
static dds_entity_t pub_participant;
static dds_entity_t pub_read_cond;
static RoundTripModule_DataType pub_pub_data;
static RoundTripModule_DataType pub_sub_data[MAX_SAMPLES];
static void *pub_samples[MAX_SAMPLES];
static dds_sample_info_t pub_info[MAX_SAMPLES];

static dds_entity_t pub_waitset;
static void pub_CtrlHandler (int sig)
{
  (void)sig;
  dds_waitset_set_trigger (pub_waitset, true);
}

// Subscriber
static dds_entity_t sub_participant;
static dds_entity_t sub_reader;
static dds_entity_t sub_writer;
static dds_entity_t sub_read_cond;
static RoundTripModule_DataType sub_data[MAX_SAMPLES];
static void * sub_samples[MAX_SAMPLES];
static dds_sample_info_t sub_info[MAX_SAMPLES];
static dds_entity_t sub_waitset;

static void sub_CtrlHandler (int sig)
{
  (void)sig;
  dds_waitset_set_trigger (sub_waitset, true);
}

// Stats
static ExampleTimeStats round_trip;
uint32_t sample_count = 0;
char output_file[100] = "cyclone_raw_latency.csv";

// Times
static dds_time_t startTime;
static dds_time_t preWriteTime;
static dds_time_t postWriteTime;
static dds_time_t postTakeTime;
static dds_time_t elapsed = 0;

static bool warmUp = true;
FILE *fp;

static void pub_data_available(dds_entity_t rd, void *arg)
{
  dds_time_t difference = 0;
  int status;
  (void)arg;
  /* Take sample and check that it is valid */
  status = dds_take (rd, pub_samples, pub_info, MAX_SAMPLES, MAX_SAMPLES);
  if (status < 0)
    DDS_FATAL("dds_take: %s\n", dds_strretcode(-status));
  postTakeTime = dds_time ();

  /* Update stats */
  difference = (postTakeTime - pub_info[0].source_timestamp);  // In nanoseconds;
  round_trip = *exampleAddTimingToTimeStats (&round_trip, difference);

  preWriteTime = dds_time();
  status = dds_write_ts (pub_writer, &pub_pub_data, preWriteTime);
  if (status < 0)
    DDS_FATAL("dds_write_ts: %s\n", dds_strretcode(-status));
  postWriteTime = dds_time();
}

static void sub_data_available(dds_entity_t rd, void *arg)
{
  int status, samplecount;
  (void)arg;
  samplecount = dds_take (rd, sub_samples, sub_info, MAX_SAMPLES, MAX_SAMPLES);
  if (samplecount < 0)
    DDS_FATAL("dds_take: %s\n", dds_strretcode(-samplecount));
  for (int j = 0; !dds_triggered (sub_waitset) && j < samplecount; j++)
  {
    /* If writer has been disposed terminate pong */

    if (sub_info[j].instance_state == DDS_IST_NOT_ALIVE_DISPOSED)
    {
      printf ("Received termination request. Terminating.\n");
      dds_waitset_set_trigger (sub_waitset, true);
      break;
    }
    else if (sub_info[j].valid_data)
    {
      /* If sample is valid, send it back to ping */
      RoundTripModule_DataType * valid_sample = &sub_data[j];
      status = dds_write_ts (sub_writer, valid_sample, sub_info[j].source_timestamp);
      if (status < 0)
        DDS_FATAL("dds_write_ts: %d\n", -status);
    }
  }
}

void *pub_main (void *args)
{
  latency_args *arguments = args;
  uint32_t payloadSize = arguments->payloadSize;
  uint64_t numSamples = arguments->numSamples;
  dds_time_t timeOut = arguments->timeOut;
  bool use_listener = arguments->use_listener;
  free(arguments);

  dds_time_t time;
  dds_time_t difference = 0;

  dds_attach_t wsresults[1];
  size_t wsresultsize = 1U;
  dds_time_t waitTimeout = DDS_SECS (1);
  unsigned long i;
  int status;

  dds_listener_t *listener = NULL;

  /* Register handler for Ctrl-C */
  struct sigaction sat, oldAction;
  sat.sa_handler = pub_CtrlHandler;
  sigemptyset (&sat.sa_mask);
  sat.sa_flags = 0;
  sigaction (SIGINT, &sat, &oldAction);

  exampleInitTimeStats (&round_trip);

  memset (&pub_sub_data, 0, sizeof (pub_sub_data));
  memset (&pub_pub_data, 0, sizeof (pub_pub_data));

  for (i = 0; i < MAX_SAMPLES; i++)
  {
    pub_samples[i] = &pub_sub_data[i];
  }

  pub_participant = dds_create_participant (DDS_DOMAIN_DEFAULT, NULL, NULL);
  if (pub_participant < 0)
    DDS_FATAL("dds_create_participant: %s\n", dds_strretcode(-pub_participant));

  if (use_listener)
  {
    listener = dds_create_listener(NULL);
    dds_lset_data_available(listener, pub_data_available);
  }
  pub_prepare_dds(&pub_writer, &pub_reader, &pub_read_cond, listener);

  pub_pub_data.payload._length = payloadSize;
  pub_pub_data.payload._buffer = payloadSize ? dds_alloc (payloadSize) : NULL;
  pub_pub_data.payload._release = true;
  pub_pub_data.payload._maximum = 0;
  for (i = 0; i < payloadSize; i++)
  {
    pub_pub_data.payload._buffer[i] = 'a';
  }

  startTime = dds_time ();
  printf ("[Publisher] Waiting for startup jitter to stabilise\n");
  fflush (stdout);
  /* Write a sample that pong can send back */
  while (!dds_triggered (pub_waitset) && difference < DDS_SECS(5))
  {
    status = dds_waitset_wait (pub_waitset, wsresults, wsresultsize, waitTimeout);
    if (status < 0)
      DDS_FATAL("dds_waitset_wait: %s\n", dds_strretcode(-status));

    if (status > 0 && listener == NULL) /* data */
    {
      status = dds_take (pub_reader, pub_samples, pub_info, MAX_SAMPLES, MAX_SAMPLES);
      if (status < 0)
        DDS_FATAL("dds_take: %s\n", dds_strretcode(-status));
    }

    time = dds_time ();
    difference = time - startTime;
  }
  if (!dds_triggered (pub_waitset))
  {
    warmUp = false;
    printf("[Publisher] Warm up complete.\n");
    fflush (stdout);
  }

  exampleResetTimeStats (&round_trip);
  startTime = dds_time ();
  /* Write a sample that pong can send back */
  preWriteTime = dds_time ();
  status = dds_write_ts (pub_writer, &pub_pub_data, preWriteTime);
  if (status < 0)
    DDS_FATAL("dds_write_ts: %s\n", dds_strretcode(-status));
  postWriteTime = dds_time ();
  for (i = 0; !dds_triggered (pub_waitset) && (!numSamples || i < numSamples) && !(timeOut && elapsed >= timeOut); i++)
  {
    status = dds_waitset_wait (pub_waitset, wsresults, wsresultsize, waitTimeout);
    if (status < 0)
      DDS_FATAL("dds_waitset_wait: %s\n", dds_strretcode(-status));
    if (status != 0 && listener == NULL) {
      pub_data_available(pub_reader, NULL);
    }
  }

  /* Log to file */
  fp = fopen(output_file, "a");
  for (unsigned long i = 0; i < round_trip.count; i++)
  {
    double latency = ((double)round_trip.values[i] / DDS_NSECS_IN_USEC) / 2.0;
    fprintf(fp, "%u,%u,%f\n", ++sample_count, payloadSize, latency);
  }
  fclose(fp);
  printf("[Publisher] Log generated in: %s\n", output_file);
  fflush (stdout);

  sigaction (SIGINT, &oldAction, 0);
  pub_finalize_dds(pub_participant);

  /* Clean up */
  exampleDeleteTimeStats (&round_trip);
  for (i = 0; i < MAX_SAMPLES; i++)
  {
    RoundTripModule_DataType_free (&pub_sub_data[i], DDS_FREE_CONTENTS);
  }
  RoundTripModule_DataType_free (&pub_pub_data, DDS_FREE_CONTENTS);

  return EXIT_SUCCESS;
}

void *sub_main (void *args)
{
  latency_args *arguments = args;
  bool use_listener = arguments->use_listener;
  free(arguments);

  dds_duration_t waitTimeout = DDS_INFINITY;
  unsigned int i;
  int status;
  dds_attach_t wsresults[1];
  size_t wsresultsize = 1U;

  dds_listener_t *listener = NULL;

  /* Register handler for Ctrl-C */
  struct sigaction sat, oldAction;
  sat.sa_handler = sub_CtrlHandler;
  sigemptyset (&sat.sa_mask);
  sat.sa_flags = 0;
  sigaction (SIGINT, &sat, &oldAction);

  /* Initialize sample data */
  memset (sub_data, 0, sizeof (sub_data));
  for (i = 0; i < MAX_SAMPLES; i++)
  {
    sub_samples[i] = &sub_data[i];
  }

  sub_participant = dds_create_participant (DDS_DOMAIN_DEFAULT, NULL, NULL);
  if (sub_participant < 0)
    DDS_FATAL("dds_create_participant: %s\n", dds_strretcode(-sub_participant));

  if (use_listener)
  {
    listener = dds_create_listener(NULL);
    dds_lset_data_available(listener, sub_data_available);
  }

  (void)sub_prepare_dds(&sub_writer, &sub_reader, &sub_read_cond, listener);

  while (!dds_triggered (sub_waitset))
  {
    /* Wait for a sample from ping */

    status = dds_waitset_wait (sub_waitset, wsresults, wsresultsize, waitTimeout);
    if (status < 0)
      DDS_FATAL("dds_waitset_wait: %s\n", dds_strretcode(-status));

    /* Take samples */
    if (listener == NULL) {
      sub_data_available (sub_reader, 0);
    }
  }

  sigaction (SIGINT, &oldAction, 0);

  /* Clean up */
  sub_finalize_dds(sub_participant, sub_data);
  fflush(stdout);

  return EXIT_SUCCESS;
}

static dds_entity_t pub_prepare_dds(dds_entity_t *wr, dds_entity_t *rd, dds_entity_t *rdcond, dds_listener_t *listener)
{
  dds_return_t status;
  dds_entity_t topic;
  dds_entity_t publisher;
  dds_entity_t subscriber;

  const char *pubPartitions[] = { "ping" };
  const char *subPartitions[] = { "pong" };
  dds_qos_t *pubQos;
  dds_qos_t *dwQos;
  dds_qos_t *drQos;
  dds_qos_t *subQos;

  /* A DDS_Topic is created for our sample type on the domain pub_participant. */
  topic = dds_create_topic (pub_participant, &RoundTripModule_DataType_desc, "RoundTrip", NULL, NULL);
  if (topic < 0)
    DDS_FATAL("dds_create_topic: %s\n", dds_strretcode(-topic));

  /* A DDS_Publisher is created on the domain pub_participant. */
  pubQos = dds_create_qos ();
  dds_qset_partition (pubQos, 1, pubPartitions);

  publisher = dds_create_publisher (pub_participant, pubQos, NULL);
  if (publisher < 0)
    DDS_FATAL("dds_create_publisher: %s\n", dds_strretcode(-publisher));
  dds_delete_qos (pubQos);

  /* A DDS_DataWriter is created on the Publisher & Topic with a modified Qos. */
  dwQos = dds_create_qos ();
  dds_qset_reliability (dwQos, DDS_RELIABILITY_RELIABLE, DDS_SECS (10));
  dds_qset_writer_data_lifecycle (dwQos, false);
  *wr = dds_create_writer (publisher, topic, dwQos, NULL);
  if (*wr < 0)
    DDS_FATAL("dds_create_writer: %s\n", dds_strretcode(-*wr));
  dds_delete_qos (dwQos);

  /* A DDS_Subscriber is created on the domain pub_participant. */
  subQos = dds_create_qos ();

  dds_qset_partition (subQos, 1, subPartitions);

  subscriber = dds_create_subscriber (pub_participant, subQos, NULL);
  if (subscriber < 0)
    DDS_FATAL("dds_create_subscriber: %s\n", dds_strretcode(-subscriber));
  dds_delete_qos (subQos);
  /* A DDS_DataReader is created on the Subscriber & Topic with a modified QoS. */
  drQos = dds_create_qos ();
  dds_qset_reliability (drQos, DDS_RELIABILITY_RELIABLE, DDS_SECS(10));
  *rd = dds_create_reader (subscriber, topic, drQos, listener);
  if (*rd < 0)
    DDS_FATAL("dds_create_reader: %s\n", dds_strretcode(-*rd));
  dds_delete_qos (drQos);

  pub_waitset = dds_create_waitset (pub_participant);
  if (listener == NULL) {
    *rdcond = dds_create_readcondition (*rd, DDS_ANY_STATE);
    status = dds_waitset_attach (pub_waitset, *rdcond, *rd);
    if (status < 0)
      DDS_FATAL("dds_waitset_attach: %s\n", dds_strretcode(-status));
  } else {
    *rdcond = 0;
  }
  status = dds_waitset_attach (pub_waitset, pub_waitset, pub_waitset);
  if (status < 0)
    DDS_FATAL("dds_waitset_attach: %s\n", dds_strretcode(-status));

  return pub_participant;
}

static void pub_finalize_dds(dds_entity_t ppant)
{
  dds_return_t status;
  status = dds_delete (ppant);
  if (status < 0)
    DDS_FATAL("dds_delete: %s\n", dds_strretcode(-status));
}

static void sub_finalize_dds(dds_entity_t pp, RoundTripModule_DataType xs[MAX_SAMPLES])
{
  dds_return_t status;
  status = dds_delete (pp);
  if (status < 0)
    DDS_FATAL("dds_delete: %s\n", dds_strretcode(-status));
  for (unsigned int i = 0; i < MAX_SAMPLES; i++)
  {
    RoundTripModule_DataType_free (&xs[i], DDS_FREE_CONTENTS);
  }
}

static dds_entity_t sub_prepare_dds(dds_entity_t *wr, dds_entity_t *rd, dds_entity_t *rdcond, dds_listener_t *rdlist)
{
  const char *pubPartitions[] = { "pong" };
  const char *subPartitions[] = { "ping" };
  dds_qos_t *qos;
  dds_entity_t subscriber;
  dds_entity_t publisher;
  dds_entity_t topic;
  dds_return_t status;

  /* A DDS Topic is created for our sample type on the domain sub_participant. */

  topic = dds_create_topic (sub_participant, &RoundTripModule_DataType_desc, "RoundTrip", NULL, NULL);
  if (topic < 0)
    DDS_FATAL("dds_create_topic: %s\n", dds_strretcode(-topic));

  /* A DDS Publisher is created on the domain sub_participant. */

  qos = dds_create_qos ();
  dds_qset_partition (qos, 1, pubPartitions);

  publisher = dds_create_publisher (sub_participant, qos, NULL);
  if (publisher < 0)
    DDS_FATAL("dds_create_publisher: %s\n", dds_strretcode(-publisher));
  dds_delete_qos (qos);

  /* A DDS DataWriter is created on the Publisher & Topic with a modififed Qos. */

  qos = dds_create_qos ();
  dds_qset_reliability (qos, DDS_RELIABILITY_RELIABLE, DDS_SECS(10));
  dds_qset_writer_data_lifecycle (qos, false);
  *wr = dds_create_writer (publisher, topic, qos, NULL);
  if (*wr < 0)
    DDS_FATAL("dds_create_writer: %s\n", dds_strretcode(-*wr));
  dds_delete_qos (qos);

  /* A DDS Subscriber is created on the domain sub_participant. */

  qos = dds_create_qos ();
  dds_qset_partition (qos, 1, subPartitions);

  subscriber = dds_create_subscriber (sub_participant, qos, NULL);
  if (subscriber < 0)
    DDS_FATAL("dds_create_subscriber: %s\n", dds_strretcode(-subscriber));
  dds_delete_qos (qos);

  /* A DDS DataReader is created on the Subscriber & Topic with a modified QoS. */

  qos = dds_create_qos ();
  dds_qset_reliability (qos, DDS_RELIABILITY_RELIABLE, DDS_SECS(10));
  *rd = dds_create_reader (subscriber, topic, qos, rdlist);
  if (*rd < 0)
    DDS_FATAL("dds_create_reader: %s\n", dds_strretcode(-*rd));
  dds_delete_qos (qos);

  sub_waitset = dds_create_waitset (sub_participant);
  if (rdlist == NULL) {
    *rdcond = dds_create_readcondition (*rd, DDS_ANY_STATE);
    status = dds_waitset_attach (sub_waitset, *rdcond, *rd);
    if (status < 0)
      DDS_FATAL("dds_waitset_attach: %s\n", dds_strretcode(-status));
  } else {
    *rdcond = 0;
  }
  status = dds_waitset_attach (sub_waitset, sub_waitset, sub_waitset);
  if (status < 0)
    DDS_FATAL("dds_waitset_attach: %s\n", dds_strretcode(-status));

  printf ("[Subscriber] Waiting for samples from ping to send back...\n");
  fflush (stdout);

  return sub_participant;
}

int main (int argc, char *argv[])
{
  uint32_t payloadSize = 0;
  uint64_t numSamples = 0;
  bool invalidargs = false;
  dds_time_t timeOut = 0;
  int argidx = 1;

  bool use_listener = false;

  /* poor man's getopt works even on Windows */
  if (argc > argidx && strcmp(argv[argidx], "-l") == 0)
  {
    argidx++;
    use_listener = true;
  }

  if (argc - argidx == 0)
  {
    invalidargs = true;
  }
  if (argc - argidx >= 1)
  {
    payloadSize = (uint32_t) atol (argv[argidx]);

    if (payloadSize > 100 * 1048576)
    {
      invalidargs = true;
    }
  }
  if (argc - argidx >= 2)
  {
    numSamples = (uint64_t) atol (argv[argidx+1]);
  }
  if (argc - argidx >= 3)
  {
    timeOut = atol (argv[argidx+2]);
  }
  if (argc - argidx >= 4)
  {
    // output_file = argv[argidx+3];
    strncpy(output_file, argv[argidx+3], 100);
  }
  if (invalidargs || (argc - argidx == 1 && (strcmp (argv[argidx], "-h") == 0 || strcmp (argv[argidx], "--help") == 0)))
    usage();

  printf("RoundtripIntraprocess run with arguments:\n");
  printf(
    "  Payload: %u\n  Number of samples: %lu\n  Timeout: %lu\n  Use listener: %d\n  Output CSV: %s\n",
    payloadSize,
    numSamples,
    timeOut,
    use_listener,
    output_file
  );
  printf("-------------------------\n");
  fflush (stdout);
  fp = fopen(output_file, "w");
  fprintf(fp, "Sample,Payload [Bytes],Latency [us]\n");
  fclose(fp);

  latency_args *pub_args = malloc(sizeof *pub_args);
  pub_args->payloadSize = payloadSize;
  pub_args->numSamples = numSamples;
  pub_args->timeOut = timeOut;
  pub_args->use_listener = use_listener;

  latency_args *sub_args = malloc(sizeof *sub_args);
  sub_args->payloadSize = payloadSize;
  sub_args->numSamples = numSamples;
  sub_args->timeOut = timeOut;
  sub_args->use_listener = use_listener;


  pthread_t pub_thread_id;
  pthread_t sub_thread_id;
  pthread_create(&pub_thread_id, NULL, pub_main, pub_args);
  pthread_create(&sub_thread_id, NULL, sub_main, sub_args);
  pthread_join(pub_thread_id, NULL);
  pthread_kill(sub_thread_id, SIGINT);

  free(pub_args);
  free(sub_args);

  printf("-------------------------\n");
  fflush (stdout);
  return EXIT_SUCCESS;
}
