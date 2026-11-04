package com;

/** The bean of the handout: one property, set by jsp:setProperty and read by jsp:getProperty. */
public class Hello {
    private String name;

    public Hello() {
        name = null;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }
}
