- [ ] Integrate Google Books Api

  - [x] Fetch book data based on user input
    - [x] fetch on click of more button
    - [x] Display book details (title, author, cover image)
  - [x] Handle API errors gracefully

  - [ ] Implement pagination
    - [x] Display 10 books per page
    - [x] Implement "Load More" button to fetch next set of books
  - [ ] Implement auto complete on search entry based on db entries

- [x] Implement user authentication

  - [x] populate with userinfo from google account

- [ ] Profile search

  - [ ] Implement search functionality to find other users
  - [ ] Display user profiles with their book collections
  - [ ] Allow users to follow/unfollow other users

- [ ] Implement archive.org API

  - [x] fetch results from iabookscollection
  - [ ] incorporate alternative collections when no records are found for a title
  - [x] Handle ampersands in title

- [ ] OpenAi Assistant

  - [ ] file handling
  - [ ] conversation

- [x] Handle non-json in response
- [ ] build out semantic caching
- [ ] .pdf handling
  - [ ] check if the record contains a pdf
  - [ ] do we store references?
  - [ ] how do we temporarily store downloaded .pdfs? Do we at all?
  - [ ] Handle .epub files
