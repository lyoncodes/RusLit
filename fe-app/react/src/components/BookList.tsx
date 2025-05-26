import Book from '../types/Book';

export const BookList = ({ books }: { books: Book[] }) => {
  if (!books || books.length === 0) {
    return <p>No books available.</p>;
  }

  return (
    <>
      <h2>Your Saved Resources</h2>
      <ul>
        {books.map((book) => (
          <li key={book.id}>
            <strong>{book.title}</strong> by {book.author}
          </li>
        ))}
      </ul>
    </>
  );
};
