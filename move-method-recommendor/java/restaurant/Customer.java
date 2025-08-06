package java.restaurant;

public class Customer {
    private final String name;
    private final String contact;

    public Customer(String n, String c) {
        name = n; contact = c;
    }

    public String getName() { return name; }
    public String getContact() { return contact; }

    public void notify(String msg) {
        NotificationService.notify(this, msg);
    }
}
