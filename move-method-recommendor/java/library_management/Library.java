package java.library_management;

import java.util.ArrayList;
import java.util.List;

public class Library {
    private List<Book> inventory = new ArrayList<>();

    public void addBook(Book book) {
        inventory.add(book);
    }

    public List<Book> getAvailableBooks() {
        List<Book> available = new ArrayList<>();
        for (Book book : inventory) {
            if (book.isAvailable()) {
                available.add(book);
            }
        }
        return available;
    }

    public void displayInventory() {
        for (Book book : inventory) {
            System.out.println(book.getTitle() + " by " + book.getAuthor() + (book.isAvailable() ? " (Available)" : " (Borrowed)"));
        }
    }
}
