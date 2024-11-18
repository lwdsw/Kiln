export type SampleData = {
  input: string
}

export type SampleDataNode = {
  topic: string
  sub_topics: SampleDataNode[]
  samples: SampleData[]
}
