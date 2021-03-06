##############################################################################
C 语言实现哈希表
##############################################################################

源文件参考 ： https://github.com/jamesroutley/write-a-hash-table

本教程由 `James Routley`_ 撰写 ， 是他在 routley.io 上发表的博客 。 本人学习过程中将\
其用中文记录下来 。 

.. _`James Routley`: https://twitter.com/james_routley

哈希表_ 是最有用的数据结构之一 。 它们快速 ， 可扩展的插入 ， 搜索和删除功能使它们与\
大量计算机科学问题相关 。 

.. _哈希表: https://en.wikipedia.org/wiki/Hash_table

在本教程中 ， 我们将使用 C 语言实现一个开放地址的双散列表 。 通过学习本教程 ， 您将\
获得 ： 

- 了解基本数据结构如何在后台运行
- 深入了解何时使用哈希表 ， 何时不使用哈希表 ， 以及哈希表会如何失效
- 接触新的 C 代码

C 是一种编写哈希表的好语言 ， 因为 ： 

- 这种语言不包含任何一种
- 它是一种低级别的语言，因此你可以更深入地了解事物在机器层面的工作方式

本教程假定您对编程和 C 语法有一定的了解 。 代码本身相对简单明了 ， 大多数问题都可以\
通过网络搜索解决 。 如果您遇到其他问题 ， 请打开 GitHub Issue_ 。

.. _Issue: https://github.com/jamesroutley/write-a-hash-table/issues

完整的实现大约需要 200 行代码 ， 大约需要一两个小时才能完成 。 

**目录结构**

1. `简介`_
2. `哈希表结构`_
3. `哈希函数`_
4. `处理碰撞`_
5. `哈希表方法`_
6. `调整表格大小`_
7. `附录：替代碰撞处理`_

.. _`简介`: #id15
.. _`哈希表结构`:
.. _`哈希函数`:
.. _`处理碰撞`:
.. _`哈希表方法`:
.. _`调整表格大小`:
.. _`附录：替代碰撞处理`:

.. contents::

******************************************************************************
01  简介
******************************************************************************

哈希表是一种数据结构 ， 它提供了 `关联数组 API`_ 的快速实现 。 由于有关哈希表的术语\
可能令人困惑 ， 因此我在下面添加了一个 摘要_ 。

.. _`关联数组 API`: #id16
.. _摘要: #id19

哈希表由一组 "桶" 组成 ， 每个桶存储一个键值对 。 为了定位应该存储键值对的桶 ， 键被\
传递给一个散列函数 。 此函数返回一个整数 ， 用作存储桶数组中该对的索引 。 当我们想要\
检索一个键值对时 ， 我们将键提供给同一个散列函数 ， 接收它的索引 ， 并使用索引在数组\
中找到它 。 

数组索引的算法复杂度为 O(1) ， 这使得哈希表在存储和检索数据时速度很快 。

我们的哈希表将字符串键映射到字符串值 ， 但这里给出的原则适用于将任意键类型映射到任意\
值类型的哈希表 。 仅支持 ASCII 字符串 ， 因为支持 unicode 非常重要并且超出了本教程\
的范围 。 

API
==============================================================================

关联数组是无序键值对的集合 。 不允许使用重复的 Key 。 支持以下操作 ： 

- ``search(a, k)`` : 从关联数组 ``a`` 中返回与键 ``k`` 关联的值 ``v`` ， 如果键不\
  存在 ， 则返回 ``NULL`` 。
- ``insert(a, k, v)`` : 将 ``k:v`` 对存储在关联数组 ``a`` 中 。 
- ``delete(a, k)`` : 删除与 ``k`` 关联的 ``k:v`` 对 ， 如果 ``k`` 不存在 ， 则不\
  执行任何操作 。 

Setup
==============================================================================

要在您的计算机上设置 C ， 请参阅 《`Build Your Own Lisp`_》 一书中 Daniel Holden \
的 `指南`_ 。 Build Your Own Lisp 是一本好书 ， 我建议你通读它 。 

.. _`Build Your Own Lisp`: http://www.buildyourownlisp.com/chapter2_installation
.. _`指南`: https://github.com/jamesroutley/write-a-hash-table/blob/master/orangeduck

Code structure
==============================================================================

代码应放在以下目录结构中 : 

.. code-block:: bash 

    .
    ├── build
    └── src
        ├── hash_table.c
        ├── hash_table.h
        ├── prime.c
        └── prime.h

``src`` 将包含我们的代码 ， ``build`` 将包含我们编译的二进制文件 。 

术语
==============================================================================

有很多名称可以互换使用 。 在本文中 ， 我们将使用以下内容 ： 

- 关联数组 ： 实现上述 API_ 的抽象数据结构 。 也称为地图 、 符号表或字典 。 
- 哈希表 ： 使用哈希函数的关联数组 API 的快速实现 。 也称为哈希映射 、 映射 、 哈希\
  或字典 。 

关联数组可以用许多不同的底层数据结构来实现 。 可以通过简单地将项目存储在数组中并在搜\
索时遍历数组来实现 (不考虑性能) 。 关联数组和哈希表经常被混淆 ， 因为关联数组经常被\
实现为哈希表 。 

.. _API: #id16

下一节 ： 哈希表结构

******************************************************************************
02  哈希表结构
******************************************************************************

我们的键值对 (条目) 将每个都存储在一个结构中 ： 

.. code-block:: c 

    // hash_table.h
    typedef struct {
        char* key;
        char* value;
    } ht_item;

我们的哈希表存储了一个指向条目的指针数组 ， 以及一些关于它的大小和它是否装满的细节 ：

.. code-block:: C 

    // hash_table.h
    typedef struct {
        int size;
        int count;
        ht_item** items;
    } ht_hash_table;

初始化和删除
==============================================================================

我们需要为 ``ht_items`` 定义初始化函数 。 这个函数分配了一个与 ``ht_item`` 大小相\
当的内存块 ， 并在新的内存块中保存了字符串 ``k`` 和 ``v`` 的副本 。 这个函数被标记\
为静态的 ， 因为它只会被哈希表内部的代码调用 。 

.. code-block:: C 

    // hash_table.c
    #include <stdlib.h>
    #include <string.h>

    #include "hash_table.h"

    static ht_item* ht_new_item(const char* k, const char* v) {
        ht_item* i = malloc(sizeof(ht_item));
        i->key = strdup(k);
        i->value = strdup(v);
        return i;
    }

``ht_new`` 初始化一个新的哈希表 。 ``size`` 定义了我们可以存储多少个条目 。 目前固\
定为 53 。 我们将在有关 调整大小_ 的部分对此进行扩展 。 我们使用 calloc 初始化项目数组 \
， 它用 ``NULL`` 字节填充分配的内存 。 数组中的 ``NULL`` 条目表示该存储桶为空 。 

.. _调整大小: waiting

.. code-block:: C 

    // hash_table.c
    ht_hash_table* ht_new() {
        ht_hash_table* ht = malloc(sizeof(ht_hash_table));

        ht->size = 53;
        ht->count = 0;
        ht->items = calloc((size_t)ht->size, sizeof(ht_item*));
        return ht;
    }

我们还需要有删除 ``ht_items`` 和 ``ht_hash_tables`` 的函数 ， 它将释放我们分配的\
内存 ， 所以我们不会导致 内存泄漏_ 。

.. _内存泄露: https://en.wikipedia.org/wiki/Memory_leak

.. code-block:: C 

    // hash_table.c
    static void ht_del_item(ht_item* i) {
        free(i->key);
        free(i->value);
        free(i);
    }


    void ht_del_hash_table(ht_hash_table* ht) {
        for (int i = 0; i < ht->size; i++) {
            ht_item* item = ht->items[i];
            if (item != NULL) {
                ht_del_item(item);
            }
        }
        free(ht->items);
        free(ht);
    }

我们已经编写了定义哈希表的代码 ， 并让我们创建和销毁一个 。 虽然目前它没有做太多事\
情 ， 但我们仍然可以尝试一下 。 

.. code-block:: C 

    // main.c
    #include "hash_table.h"


    int main() {
        ht_hash_table* ht = ht_new();
        printf("%d, %d, %s, %s", ht->count, ht->size, ht->items[0], ht->items[1]);
        ht_del_hash_table(ht);
    }

下一节 ： 哈希函数

******************************************************************************
03  哈希函数
******************************************************************************

在本节中 ， 我们将编写我们的哈希函数 。 

我们选择的哈希函数应该 ： 

- 将一个字符串作为输入并返回一个介于 0 和 m 之间的数字 ， 即我们想要的桶数组长度 。 
- 为一组平均输入返回桶索引的均匀分布 。 如果我们的哈希函数分布不均 ， 它会在某些桶中\
  放入比其他桶更多的条目 。 这将导致更高的碰撞率 。 冲突会降低我们哈希表的效率 。 

算法
==============================================================================

我们将使用一个通用的字符串散列函数 ， 用伪代码表示如下 。 

.. code-block:: C 

    function hash(string, a, num_buckets):
        hash = 0
        string_len = length(string)
        for i = 0, 1, ..., string_len:
            hash += (a ** (string_len - (i+1))) * char_code(string[i])
        hash = hash % num_buckets
        return hash

这个哈希函数有两个步骤 ：

- 将字符串转换为大整数
- 通过取余数 ``mod m`` 将整数的大小减小到固定范围

变量 a 应该是一个大于字母表大小的素数 。 我们正在散列 ASCII 字符串 ， 它的字母大小\
为 128 ， 所以我们应该选择一个比这更大的素数 。 

``char_code`` 是一个函数 ， 它返回一个表示字符的整数 。 为此 ， 我们将使用 ASCII \
字符代码 。 

让我们试试哈希函数 ：

.. code-block:: C 

    hash("cat", 151, 53)

    hash = (151**2 * 99 + 151**1 * 97 + 151**0 * 116) % 53
    hash = (2257299 + 14647 + 116) % 53
    hash = (2272062) % 53
    hash = 5

改变 a 的值会给我们一个不同的哈希函数 。 

.. code-block:: c 

    hash("cat", 163, 53) = 3

实现
==============================================================================

.. code-block:: C 

    // hash_table.c
    static int ht_hash(const char* s, const int a, const int m) {
        long hash = 0;
        const int len_s = strlen(s);
        for (int i = 0; i < len_s; i++) {
            hash += (long)pow(a, len_s - (i+1)) * s[i];
            hash = hash % m;
        }
        return (int)hash;
    }

不可控数据
==============================================================================

理想的散列函数将始终返回均匀分布 。 但是 ， 对于任何散列函数 ， 都有一组 "不可控" 输\
入 ， 它们都散列到相同的值 。 要找到这组输入 ， 请通过该函数运行大量输入 。 散列到特\
定桶的所有输入形成不可控数据集 。 

不可控输入集的存在意味着所有输入都没有完美的哈希函数 。 我们能做的最好的事情就是创建\
一个对预期数据集表现良好的函数 。 

不可控输入也带来了安全问题 。 如果某个恶意用户向哈希表提供了一组冲突的键 ， 那么搜索\
这些键将花费比正常时间 (``O(1)``) 更长的时间 (``O(n)``) 。 这可以用作针对以哈希表为\
基础的系统的拒绝服务攻击 ， 例如 DNS 和某些 Web 服务 。 

下一节 ： 处理碰撞

******************************************************************************
04  处理碰撞
******************************************************************************

哈希函数将无限数量的输入映射到有限数量的输出 。 不同的输入键会映射到相同的数组索引 \
， 导致桶冲突 。 哈希表必须实现一些处理冲突的方法 。 

我们的哈希表将使用一种称为双散列开放寻址的技术来处理冲突 。 双散列使用两个散列函数来\
计算在 ``i`` 次碰撞后应存储项目的索引 。 

有关其他类型碰撞解决方案的概述，请参见 附录_ 。

.. _附录:

双重散列
==============================================================================

在 ``i`` 次碰撞后应该使用的索引由下式给出 ： 

.. code-block:: C 

    index = hash_a(string) + i * hash_b(string) % num_buckets

我们看到 ， 如果没有发生冲突 ， ``i = 0`` ， 所以索引只是字符串的 ``hash_a`` 。 如\
果发生冲突 ， ``hash_b`` 会修改索引 。 

``hash_b`` 有可能返回 0 ， 将第二项减少到 0 。 这将导致哈希表一遍又一遍地尝试将项目\
插入到同一个桶中 。 我们可以通过将第二个哈希的结果加 1 来缓解这种情况 ， 确保它永远\
不会为 0 。 

.. code-block:: C

    index = (hash_a(string) + i * (hash_b(string) + 1)) % num_buckets

代码实现
==============================================================================

.. code-block:: C 

    // hash_table.c
    static int ht_get_hash(
        const char* s, const int num_buckets, const int attempt
    ) {
        const int hash_a = ht_hash(s, HT_PRIME_1, num_buckets);
        const int hash_b = ht_hash(s, HT_PRIME_2, num_buckets);
        return (hash_a + (attempt * (hash_b + 1))) % num_buckets;
    }

下一节 ： 哈希表方法

******************************************************************************
05  哈希表方法
******************************************************************************

我们的哈希函数将实现以下 API ： 

.. code-block:: c

    // hash_table.h
    void ht_insert(ht_hash_table* ht, const char* key, const char* value);
    char* ht_search(ht_hash_table* ht, const char* key);
    void ht_delete(ht_hash_table* h, const char* key);

插入
==============================================================================

为了插入一个新的键值对 ， 我们遍历索引直到找到一个空桶 。 然后我们将项目插入到该存储\
桶中并增加哈希表的 ``count`` 属性 ， 以指示已添加新项目 。 当我们在下一节中查看 \
resizing_ 大小时 ， 哈希表的 ``count`` 属性将变得有用 。 

.. _resizing:

.. code-block:: C 

    // hash_table.c
    void ht_insert(ht_hash_table* ht, const char* key, const char* value) {
        ht_item* item = ht_new_item(key, value);
        int index = ht_get_hash(item->key, ht->size, 0);
        ht_item* cur_item = ht->items[index];
        int i = 1;
        while (cur_item != NULL) {
            index = ht_get_hash(item->key, ht->size, i);
            cur_item = ht->items[index];
            i++;
        } 
        ht->items[index] = item;
        ht->count++;
    }

搜索
==============================================================================

搜索类似于插入 ， 但在 ``while`` 循环的每次迭代中 ， 我们检查项目的键是否与我们正在\
搜索的键匹配 。 如果是 ， 我们返回项目的值 。 如果 while 循环命中 ``NULL`` 存储桶 \
， 我们将返回 ``NULL`` ， 以指示未找到任何值 。 

.. code-block:: C 

    // hash_table.c
    char* ht_search(ht_hash_table* ht, const char* key) {
        int index = ht_get_hash(key, ht->size, 0);
        ht_item* item = ht->items[index];
        int i = 1;
        while (item != NULL) {
            if (strcmp(item->key, key) == 0) {
                return item->value;
            }
            index = ht_get_hash(key, ht->size, i);
            item = ht->items[index];
            i++;
        } 
        return NULL;
    }

删除
==============================================================================

从一个开放寻址的哈希表中删除比插入或搜索更复杂 。 我们想删除的条目可能是一个碰撞链的\
一部分 。 从表中删除它将打破这个链 ， 并使寻找链尾的条目成为不可能 。 为了解决这个问\
题 ， 我们不会删除这个条目 ， 而是简单地把它标记为已删除 。 

我们用一个指向全局标记项的指针来标记一个项目为已删除 ， 这个全局标记项表示一个桶中包\
含一个已删除的项目 。 

.. code-block:: C 

// hash_table.c
static ht_item HT_DELETED_ITEM = {NULL, NULL};


    void ht_delete(ht_hash_table* ht, const char* key) {
        int index = ht_get_hash(key, ht->size, 0);
        ht_item* item = ht->items[index];
        int i = 1;
        while (item != NULL) {
           if (item != &HT_DELETED_ITEM) {
                if (strcmp(item->key, key) == 0) {
                    ht_del_item(item);
                    ht->items[index] = &HT_DELETED_ITEM;
                }
            }
            index = ht_get_hash(key, ht->size, i);
            item = ht->items[index];
            i++;
        } 
        ht->count--;
    }

删除后 ， 我们递减哈希表的 ``count`` 属性 。 

我们还需要修改 ``ht_insert`` 和 ``ht_search`` 函数以考虑已删除的节点 。 

搜索时 ， 我们忽略并 "跳过" 已删除的节点 。 插入的时候 ， 如果我们命中一个被删除的节\
点 ， 就可以将新节点插入到被删除的槽中 。 

.. code-block:: C 

    // hash_table.c
    void ht_insert(ht_hash_table* ht, const char* key, const char* value) {
        // ...
        while (cur_item != NULL && cur_item != &HT_DELETED_ITEM) {
            // ...
        }
        // ...
    }


    char* ht_search(ht_hash_table* ht, const char* key) {
        // ...
        while (item != NULL) {
           if (item != &HT_DELETED_ITEM) { 
                if (strcmp(item->key, key) == 0) {
                    return item->value;
                }
            }
            // ...
        }
        // ...
    }

未完待续 ...

下一篇文章 ： `下一篇`_ 

.. _`下一篇`: Hash_Table-02.rst
