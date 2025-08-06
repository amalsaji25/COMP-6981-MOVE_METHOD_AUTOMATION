package java.restaurant;

public class MenuItem {
    private final String name;
    private final double price;

    public MenuItem(String n, double p) {
        name = n;
        price = p;
    }

    public String getName() { return name; }
    public double getPrice() { return price; }
}
