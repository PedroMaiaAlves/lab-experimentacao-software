"""Definição da query GraphQL usada para coletar repositórios no GitHub."""

GRAPHQL_QUERY = """
query($queryString: String!, $first: Int!, $after: String) {
  rateLimit { remaining resetAt }
  search(query: $queryString, type: REPOSITORY, first: $first, after: $after) {
    pageInfo { hasNextPage endCursor }
    edges {
      node {
        ... on Repository {
          nameWithOwner
          url
          stargazerCount
          createdAt
          pushedAt
          primaryLanguage { name }
          pullRequests(states: MERGED) { totalCount }
          releases(first: 1, orderBy: {field: CREATED_AT, direction: DESC}) { totalCount }
          openIssues: issues(states: OPEN) { totalCount }
          closedIssues: issues(states: CLOSED) { totalCount }
        }
      }
    }
  }
}
"""
