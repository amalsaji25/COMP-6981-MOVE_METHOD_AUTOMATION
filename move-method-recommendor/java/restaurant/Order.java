package java.restaurant;


import java.util.*;

public class Order {
    private static int nextId = 1;
    private final int id;
    private final Customer customer;
    private final List<MenuItem> items;

    public Order(Customer c, List<MenuItem> i) {
        id = nextId++;
        customer = c;
        items = new ArrayList<>(i);
    }

    public int getId() { return id; }
    public Customer getCustomer() { return customer; }

    public double getTotal() {
        return items.stream().mapToDouble(MenuItem::getPrice).sum();
    }
}
