### Classes

- `kg:Movie` - a movie.
- `kg:Person` - an actor or director.
- `kg:Role` - an acting participation with character and cast-order details.
- `kg:Genre` - a movie genre.
- `kg:Country` - a movie production country.
- `kg:Language` - a language associated with a movie.
- `kg:Keyword` - a movie keyword.

### Object properties

- `kg:actor` - links a movie to a person or role, and a role to a person.
- `kg:countryOfOrigin` - links a movie to a production country.
- `kg:director` - links a movie to its director.
- `kg:genre` - links a movie to a genre.
- `kg:keywords` - links a movie to a keyword.
- `kg:inLanguage` - links a movie to its original or spoken languages.
- `kg:directedMovie` - links a director to a movie; inverse of kg:director.
- `kg:hasCastMember` - links a director to people or roles in movies they directed.
- `kg:referencePage` - links a movie to a reference webpage identifying it.

### Datatype properties

- `kg:abstract` - movie synopsis (xsd:string).
- `kg:characterName` - character name for an acting role (xsd:string).
- `kg:datePublished` - movie release date (xsd:date).
- `kg:duration` - movie runtime (xsd:duration).
- `kg:name` - entity name or movie title (xsd:string).
- `kg:position` - cast order (xsd:integer).
- `kg:ratingValue` - average rating directly on a movie (xsd:decimal).
