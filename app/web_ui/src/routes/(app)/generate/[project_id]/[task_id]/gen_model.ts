export type SampleData = {
  input: string
  saved: boolean
  model_name: string
  model_provider: string
}

export type SampleDataNode = {
  topic: string
  sub_topics: SampleDataNode[]
  samples: SampleData[]
}
