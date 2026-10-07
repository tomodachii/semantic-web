### Classes

- `schema:Movie` - a movie.
- `schema:Person` - an actor or director.
- `schema:Role` - an acting participation with character and cast-order details.
- `kg:Genre` - a movie genre.
- `schema:Country` - a movie production country.
- `schema:Language` - a language associated with a movie.
- `schema:AggregateRating` - a movie's average rating and vote count.
- `schema:DefinedTerm` - a movie keyword.

### Object properties

- `schema:actor` - links a movie to a person or role, and a role to a person.
- `schema:aggregateRating` - links a movie to its rating summary.
- `schema:countryOfOrigin` - links a movie to a production country.
- `schema:director` - links a movie to its director.
- `schema:genre` - links a movie to a genre.
- `schema:keywords` - links a movie to a keyword.
- `schema:inLanguage` - links a movie to its original or spoken languages.
- `kg:directedMovie` - links a director to a movie; inverse of schema:director.
- `kg:hasCastMember` - links a director to people or roles in movies they directed.
- `schema:sameAs` - links a movie to a reference webpage identifying it.

### Datatype properties

- `schema:abstract` - movie synopsis (xsd:string).
- `schema:characterName` - character name for an acting role (xsd:string).
- `schema:datePublished` - movie release date (xsd:date).
- `schema:duration` - movie runtime (xsd:duration).
- `schema:name` - entity name or movie title (xsd:string).
- `schema:position` - cast order (xsd:integer).
- `schema:ratingCount` - number of votes (xsd:integer).
- `schema:ratingValue` - average rating (xsd:decimal).
