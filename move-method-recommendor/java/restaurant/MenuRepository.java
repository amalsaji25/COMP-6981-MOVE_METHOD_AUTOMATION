package java.restaurant;

import java.util.*;

public class MenuRepository {
    private final List<MenuItem> items = new ArrayList<>();

    public void add(MenuItem m)    { items.add(m); }
    public void remove(MenuItem m) { items.remove(m); }
    public MenuItem findByName(String name) {
        return items.stream()
            .filter(i -> i.getName().equalsIgnoreCase(name))
            .findFirst().orElse(null);
    }
    public List<MenuItem> loadAll() {
        return new ArrayList<>(items);
    }
    public void saveAll() {
    }
}
