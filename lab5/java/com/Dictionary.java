package com;

import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

/**
 * English-Russian dictionary of a limited lexicon. The direction is chosen by the alphabet of the word:
 * Cyrillic letters mean Russian to English, anything else English to Russian.
 */
public class Dictionary {
    private static final Map<String, String> EN_RU = new LinkedHashMap<String, String>();
    private static final Map<String, String> RU_EN = new LinkedHashMap<String, String>();

    static {
        String[][] pairs = {
            {"hello", "привет"}, {"world", "мир"}, {"cat", "кот"}, {"dog", "собака"},
            {"house", "дом"}, {"book", "книга"}, {"water", "вода"}, {"bread", "хлеб"},
            {"sun", "солнце"}, {"moon", "луна"}, {"city", "город"}, {"street", "улица"},
            {"friend", "друг"}, {"teacher", "преподаватель"}, {"student", "студент"},
            {"university", "университет"}, {"computer", "компьютер"}, {"program", "программа"},
            {"server", "сервер"}, {"page", "страница"}, {"money", "деньги"}, {"rate", "курс"},
            {"bank", "банк"}, {"picture", "картинка"}, {"window", "окно"}, {"table", "стол"},
            {"red", "красный"}, {"blue", "синий"}, {"green", "зелёный"}, {"good", "хороший"},
            {"day", "день"}, {"night", "ночь"}, {"time", "время"}, {"year", "год"},
            {"read", "читать"}, {"write", "писать"}, {"work", "работа"}, {"thank you", "спасибо"},
        };
        for (String[] pair : pairs) {
            EN_RU.put(pair[0], pair[1]);
            RU_EN.put(pair[1], pair[0]);
        }
        RU_EN.put("зеленый", "green");
    }

    private String word;

    public Dictionary() {
        word = null;
    }

    public String getWord() {
        return word;
    }

    public void setWord(String word) {
        this.word = word;
    }

    private String key() {
        return word == null ? "" : word.trim().toLowerCase(Locale.ROOT).replaceAll("\\s+", " ");
    }

    public boolean isRussian() {
        for (char c : key().toCharArray()) {
            if (Character.UnicodeBlock.of(c) == Character.UnicodeBlock.CYRILLIC) {
                return true;
            }
        }
        return false;
    }

    public String getDirection() {
        return isRussian() ? "RU → EN" : "EN → RU";
    }

    public boolean isKnown() {
        return getTranslation() != null;
    }

    /** The translation or null when the word is outside the lexicon. */
    public String getTranslation() {
        return (isRussian() ? RU_EN : EN_RU).get(key());
    }

    public static Map<String, String> lexicon() {
        return EN_RU;
    }
}
