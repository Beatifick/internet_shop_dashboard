import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


# НАСТРОЙКА ПРИЛОЖЕНИЯ

st.set_page_config(
    page_title="Анализ интернет-магазина",
    page_icon="🛒",
    layout="wide"
)

st.title("Анализ эффективности интернет-магазина")


# ЗАГРУЗКА ДАННЫХ

@st.cache_data
def load_data():
    orders = pd.read_csv("orders.csv")
    users = pd.read_csv("users.csv")
    items = pd.read_csv("items.csv")

    return orders, users, items


orders, users, items = load_data()


# ОЧИСТКА И ПОДГОТОВКА ДАННЫХ

# Приводим даты к типу datetime
orders["order_date"] = pd.to_datetime(
    orders["order_date"],
    errors="coerce"
)

users["registration_date"] = pd.to_datetime(
    users["registration_date"],
    errors="coerce"
)

# Приводим числовые столбцы к числовому типу
orders["quantity"] = pd.to_numeric(
    orders["quantity"],
    errors="coerce"
)

orders["price_per_unit"] = pd.to_numeric(
    orders["price_per_unit"],
    errors="coerce"
)

items["base_price"] = pd.to_numeric(
    items["base_price"],
    errors="coerce"
)


# ОБЪЕДИНЕНИЕ ТАБЛИЦ

# Объединяем заказы с информацией о пользователях
df = orders.merge(
    users,
    on="user_id",
    how="left"
)

# Добавляем информацию о товарах
df = df.merge(
    items,
    on="item_id",
    how="left"
)


# ПРОВЕРКА И ОБРАБОТКА ПРОПУСКОВ

# Считаем количество пропусков в каждом столбце
missing_values = df.isnull().sum()

# Удаляем строки с некорректной датой,
# количеством или ценой
df = df.dropna(
    subset=[
        "order_date",
        "quantity",
        "price_per_unit"
    ]
)


# РАСЧЁТ ВЫРУЧКИ

df["revenue"] = (
    df["quantity"] * df["price_per_unit"]
)


# ПРОВЕРКА КАЧЕСТВА ДАННЫХ

with st.expander("Проверка качества данных"):

    st.write(
        "Количество пропусков после объединения таблиц:"
    )

    missing_table = (
        missing_values
        .reset_index()
    )

    missing_table.columns = [
        "Столбец",
        "Количество пропусков"
    ]

    st.dataframe(
        missing_table,
        use_container_width=True
    )

    st.write("Типы данных:")

    types_table = (
        df.dtypes
        .reset_index()
    )

    types_table.columns = [
        "Столбец",
        "Тип данных"
    ]

    st.dataframe(
        types_table,
        use_container_width=True
    )

    if missing_values.sum() == 0:
        st.success(
            "Пропуски в объединённых данных не обнаружены."
        )
    else:
        st.warning(
            "В данных обнаружены пропуски. "
            "Строки с некорректными датами, количеством "
            "и ценой были удалены."
        )


# ФИЛЬТРЫ

st.header("Фильтры")

col1, col2 = st.columns(2)


# Фильтр по дате

with col1:

    min_date = df["order_date"].min().date()
    max_date = df["order_date"].max().date()

    date_range = st.date_input(
        "Период заказов",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )


# Фильтр по категории

with col2:

    categories = [
        "Все категории"
    ] + sorted(
        df["category"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_category = st.selectbox(
        "Категория товара",
        categories
    )


# ПРИМЕНЕНИЕ ФИЛЬТРОВ

filtered_df = df.copy()


# Фильтр по дате

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:

    start_date, end_date = date_range

    filtered_df = filtered_df[
        (filtered_df["order_date"].dt.date >= start_date)
        & (filtered_df["order_date"].dt.date <= end_date)
    ]


# Фильтр по категории

if selected_category != "Все категории":

    filtered_df = filtered_df[
        filtered_df["category"] == selected_category
    ]


# КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ

total_orders = filtered_df["order_id"].nunique()

total_revenue = filtered_df["revenue"].sum()

unique_users = filtered_df["user_id"].nunique()


# Средний чек
if total_orders > 0:

    average_check = (
        total_revenue / total_orders
    )

else:

    average_check = 0


# БЛОК «КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ»

st.header("Ключевые показатели")

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Количество заказов",
        total_orders
    )


with col2:

    st.metric(
        "Общая выручка",
        f"{total_revenue:,.2f} ₽"
    )


with col3:

    st.metric(
        "Уникальные пользователи",
        unique_users
    )


with col4:

    st.metric(
        "Средний чек",
        f"{average_check:,.2f} ₽"
    )


# БЛОК «СЫРЫЕ ДАННЫЕ»

st.header("Сырые данные")

st.dataframe(
    filtered_df,
    use_container_width=True
)


# БЛОК «ВИЗУАЛИЗАЦИЯ»

st.header("Визуализация")


# ПОДГОТОВКА ДАННЫХ ДЛЯ ГРАФИКОВ

# Выручка по каждому товару
product_revenue = (
    filtered_df
    .groupby("item_name")["revenue"]
    .sum()
    .sort_values(ascending=False)
)

# Топ-10 товаров
top_products = (
    product_revenue
    .head(10)
    .sort_values()
)

# Выручка по категориям
category_revenue = (
    filtered_df
    .groupby("category")["revenue"]
    .sum()
    .sort_values(ascending=False)
)

# Порядок дней недели
weekday_order = [
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье"
]

# Перевод номера дня недели в русское название
weekday_names = {
    0: "Понедельник",
    1: "Вторник",
    2: "Среда",
    3: "Четверг",
    4: "Пятница",
    5: "Суббота",
    6: "Воскресенье"
}

# Количество уникальных заказов по дням недели
weekday_orders = (
    filtered_df
    .assign(
        weekday=filtered_df[
            "order_date"
        ].dt.dayofweek.map(weekday_names)
    )
    .groupby("weekday")["order_id"]
    .nunique()
    .reindex(
        weekday_order,
        fill_value=0
    )
)


# ТОП-10 ТОВАРОВ ПО ВЫРУЧКЕ

st.subheader("Топ-10 товаров по выручке")

if not top_products.empty:

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    top_products.plot(
        kind="barh",
        ax=ax
    )

    ax.set_title(
        "Топ-10 товаров по выручке"
    )

    ax.set_xlabel(
        "Выручка, ₽"
    )

    ax.set_ylabel(
        "Товар"
    )

    plt.tight_layout()

    st.pyplot(fig)

    plt.close(fig)

else:

    st.info(
        "Нет данных для построения графика."
    )


# ВЫРУЧКА ПО КАТЕГОРИЯМ

st.subheader("Выручка по категориям товаров")

if not category_revenue.empty:

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    category_revenue.plot(
        kind="bar",
        ax=ax
    )

    ax.set_title(
        "Выручка по категориям"
    )

    ax.set_xlabel(
        "Категория"
    )

    ax.set_ylabel(
        "Выручка, ₽"
    )

    plt.xticks(
        rotation=45,
        ha="right"
    )

    plt.tight_layout()

    st.pyplot(fig)

    plt.close(fig)

else:

    st.info(
        "Нет данных для построения графика."
    )


# КОЛИЧЕСТВО ЗАКАЗОВ ПО ДНЯМ НЕДЕЛИ

st.subheader(
    "Количество заказов по дням недели"
)

if not filtered_df.empty:

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    weekday_orders.plot(
        kind="bar",
        ax=ax
    )

    ax.set_title(
        "Количество заказов по дням недели"
    )

    ax.set_xlabel(
        "День недели"
    )

    ax.set_ylabel(
        "Количество заказов"
    )

    plt.xticks(
        rotation=45,
        ha="right"
    )

    plt.tight_layout()

    st.pyplot(fig)

    plt.close(fig)

else:

    st.info(
        "Нет данных для построения графика."
    )


# БЛОК «АНАЛИТИЧЕСКИЕ ВЫВОДЫ»

st.header("Аналитические выводы")


if not filtered_df.empty:

    # Категория с максимальной выручкой
    best_category = (
        category_revenue.idxmax()
    )

    best_category_revenue = (
        category_revenue.max()
    )


    # Товар с максимальной выручкой
    best_product = (
        product_revenue.idxmax()
    )

    best_product_revenue = (
        product_revenue.max()
    )


    # День недели с максимальным количеством заказов
    best_weekday = (
        weekday_orders.idxmax()
    )

    best_weekday_orders = (
        weekday_orders.max()
    )


    # Аналитический вывод №1

    st.markdown(
        f"""
        **1. Наибольшую выручку приносит категория
        «{best_category}».**

        Выручка этой категории составляет
        **{best_category_revenue:,.2f} ₽**.
        """
    )


    # Аналитический вывод №2

    st.markdown(
        f"""
        **2. Лидером по выручке является товар
        «{best_product}».**

        Выручка от этого товара составляет
        **{best_product_revenue:,.2f} ₽**.
        """
    )


    # Аналитический вывод №3

    st.markdown(
        f"""
        **3. Наибольшее количество заказов приходится
        на день «{best_weekday}».**

        В этот день было оформлено
        **{best_weekday_orders} заказов**.
        """
    )

else:

    st.warning(
        "После применения выбранных фильтров "
        "данных для анализа нет."
    )