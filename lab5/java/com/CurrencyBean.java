package com;

import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Exchange rate of the dollar or the euro in Belarusian roubles.
 *
 * Like com.Hello, the bean has a property "name" that jsp:setProperty fills from the form field.
 * The rate is taken from the National Bank (api.nbrb.by) once a day; without the network, or with
 * -Dlab5.offline=true, a built-in table is used, and getSource says which one answered.
 */
public class CurrencyBean {
    private static final String API = "https://api.nbrb.by/exrates/rates/%s?parammode=2";
    private static final Map<String, String> ALIASES = new HashMap<String, String>();
    private static final Map<String, String> TITLES = new HashMap<String, String>();
    private static final Map<String, Double> TABLE = new HashMap<String, Double>();
    private static final String TABLE_DATE = "2026-11-04";
    private static final Map<String, String[]> CACHE = new HashMap<String, String[]>();

    static {
        for (String alias : new String[] {"usd", "dollar", "dollars", "us dollar", "$", "доллар", "доллары", "долларов", "доллар сша"}) {
            ALIASES.put(alias, "USD");
        }
        for (String alias : new String[] {"eur", "euro", "euros", "€", "евро"}) {
            ALIASES.put(alias, "EUR");
        }
        TITLES.put("USD", "US dollar / Доллар США");
        TITLES.put("EUR", "Euro / Евро");
        TABLE.put("USD", 2.9779);
        TABLE.put("EUR", 3.3323);
    }

    private String name;
    private String code;
    private double rate;
    private String date;
    private String source;

    public CurrencyBean() {
        name = null;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
        this.code = name == null ? null : ALIASES.get(name.trim().toLowerCase(Locale.ROOT));
        if (code != null) {
            load();
        }
    }

    public boolean isKnown() {
        return code != null;
    }

    public String getCode() {
        return code == null ? "" : code;
    }

    public String getTitle() {
        return code == null ? "" : TITLES.get(code);
    }

    /** Roubles for one unit of the currency, four decimals as the National Bank publishes. */
    public String getRate() {
        return code == null ? "" : String.format(Locale.ROOT, "%.4f", rate);
    }

    public String getDate() {
        return date == null ? "" : date;
    }

    public String getSource() {
        return source == null ? "" : source;
    }

    private void load() {
        String today = java.time.LocalDate.now().toString();
        synchronized (CACHE) {
            String[] cached = CACHE.get(code);
            if (cached != null && cached[1].equals(today)) {
                apply(cached);
                return;
            }
        }
        String[] answer = null;
        if (!Boolean.getBoolean("lab5.offline")) {
            answer = fetch(code);
        }
        if (answer == null) {
            answer = new String[] {String.valueOf(TABLE.get(code)), TABLE_DATE, "table"};
        } else {
            synchronized (CACHE) {
                CACHE.put(code, answer);
            }
        }
        apply(answer);
    }

    private void apply(String[] answer) {
        rate = Double.parseDouble(answer[0]);
        date = answer[1];
        source = answer[2];
    }

    /** {rate per one unit, date, "NBRB"} or null when the API cannot be reached. */
    static String[] fetch(String code) {
        try {
            HttpURLConnection connection = (HttpURLConnection) new URL(String.format(API, code)).openConnection();
            connection.setConnectTimeout(3000);
            connection.setReadTimeout(3000);
            if (connection.getResponseCode() != 200) {
                return null;
            }
            String json;
            try (InputStream in = connection.getInputStream()) {
                ByteArrayOutputStream bytes = new ByteArrayOutputStream();
                byte[] chunk = new byte[4096];
                for (int n; (n = in.read(chunk)) > 0; ) {
                    bytes.write(chunk, 0, n);
                }
                json = new String(bytes.toByteArray(), StandardCharsets.UTF_8);
            }
            Matcher rate = Pattern.compile("\"Cur_OfficialRate\":([0-9.]+)").matcher(json);
            Matcher scale = Pattern.compile("\"Cur_Scale\":([0-9]+)").matcher(json);
            Matcher date = Pattern.compile("\"Date\":\"([0-9-]{10})").matcher(json);
            if (!(rate.find() && scale.find() && date.find())) {
                return null;
            }
            double perUnit = Double.parseDouble(rate.group(1)) / Integer.parseInt(scale.group(1));
            return new String[] {String.valueOf(perUnit), date.group(1), "NBRB"};
        } catch (Exception e) {
            return null;
        }
    }
}
