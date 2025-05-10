# Nhom5_DoAnAI_CakeCollectGame
Đồ Án môn Trí tuệ nhân tạo - HKII - 2024 - 2025

## MỤC LỤC
1. [MỞ ĐẦU](#1-mở-đầu)
   - [Phát biểu bài toán](#11-phát-biểu-bài-toán)
   - [Mục tiêu](#12-mục-tiêu)
2. [NỘI DUNG](#2-nội-dung)
   - [Tìm kiếm mù (Uninformed Search)](#21-nhóm-thuật-toán-tìm-kiếm-mù-uninformed-search-algorithms)
     - [Breadth-First Search (BFS)](#breadth-first-search-bfs)
     - [Depth-First Search (DFS)](#depth-first-search-dfs)
   - [Tìm kiếm có thông tin (Informed Search)](#22-các-thuật-toán-tìm-kiếm-có-thông-tin-informed-search-algorithms)
     - [A* Search](#a-search)
   - [Tìm kiếm cục bộ (Local Search)](#23-các-thuật-toán-tìm-kiếm-cục-bộ-local-search-algorithms)
     - [Simulated Annealing](#simulated-annealing)
   - [Tìm kiếm trong môi trường phức tạp](#24-các-thuật-toán-tìm-kiếm-trong-môi-trường-phức-tạp-complex-environment)
     - [Search in Nondeterministic (AND-OR Search)](#search-in-nondeterministic-environment)
   - [Tìm kiếm thỏa mãn ràng buộc (CSP)](#25-các-thuật-toán-tìm-kiếm-thỏa-mãn-ràng-buộc-constraint-satisfaction-problem)
     - [Backtracking with Forward Checking](#backtracking-with-forward-checking)
   - [Học tăng cường (Reinforcement Learning)](#26-các-thuật-toán-tìm-kiếm-học-tăng-cường-reinforcement-learning)
     - [Q-Learning](#q-learning)
   - [Chế độ AI Battle](#27-chế-độ-ai-battle)
3. [KẾT LUẬN](#3-kết-luận)

## 1. MỞ ĐẦU
#### 1.1. Phát biểu bài toán
Đồ án trò chơi "Cake Collect Game" được lấy ý tưởng dựa trên sự kiện "Cake Hound Round-up" của tựa game **"Cookie Run: Kingdom"**. Trò chơi yêu cầu người chơi thu thập các chuỗi bánh cùng màu liên tiếp để nhận điểm. Có năm loại bánh với năm màu sắc khác nhau được quy định về số lượng về phần thưởng khác nhau:
-	2 bánh trắng = 200 điểm
-	3 bánh sô-cô-la = 300 điểm
-	4 bánh vàng = 400 điểm
-	5 bánh xanh lá = 500 điểm 
-	6 bánh tím = 600 điểm
Mỗi người chơi có một túi có thể chứa tối đa bảy miếng bánh. Khi túi đầy, miếng bánh kế tiếp được nhặt sẽ đẩy miếng bánh nhặt đầu tiên ra theo cấu trúc hàng đợi.

#### 1.2. Mục tiêu

- Xây dựng một môi trường trò chơi "Cake Collect Game" để mô phỏng và so sánh hiệu quả của các thuật toán tìm kiếm và học tăng cường trong lĩnh vực AI. Cụ thể là thiết kế một môi trường 2D với các bánh được phân bố ngẫu nhiên trên bản đồ. Triển khai các agent sử dụng các thuật toán AI khác nhau để thu thập bánh một cách tối ưu và so sánh hiệu suất của chúng trong môi trường cạnh tranh trực tiếp (Chế độ "AI Battle!").
- Đồ án không chỉ là tiêu chí đánh giá kết quả học tập trong suốt một học kì của sinh viên, mà còn là một dự án nhỏ thể hiện khả năng của sinh viên trong việc sử dụng ngôn ngữ lập trình Python để phát triển trò chơi 2D.

## 2. Nội dung

Vì bản đồ khá rộng với kích thước 25x25, các thuật toán được bổ sung thêm max_depth để hạn chế sự bùng nổ số trạng thái cần duyệt và tăng hiệu năng, tránh một số thuật toán rơi vào vòng lặp hay để quy vô hạn.

#### 2.1. Nhóm thuật toán Tìm kiếm mù (Uninformed Search Algorithms)

Trong nhóm thuật toán này, hai thuật toán BFS và DFS được chọn làm đại diện để so sánh với các nhóm thuật toán khác.

##### Thành phần chính của bài toán tìm kiếm
- **Không gian tìm kiếm (State-Space)**: tập các giải pháp đường đi khả thi để tìm ra combo vật phẩm đạt được điểm.
- **Trạng thái ban đầu (Initial State)**: trạng thái mà tác nhân bắt đầu tìm kiếm. 
    - Trong chế độ "Play AI", tác nhân tìm kiếm được đặt ở trung tâm bản đồ với các vật phẩm được đặt ngẫu nhiên.
    - Trong chế độ "AI Battle!", các tác nhân được đặt ở ba vị trí cố định khác nhau, có thể bật/tắt ba tác nhân tùy ý và vật phẩm được đặt ngẫu nhiên.
- **Trạng thái đích (Goal State)**: điều kiện để thuật toán dừng, cũng là trạng thái mong muốn.
    - Chế độ "Play AI" trạng thái đích là khi tác nhân đã nhặt được tất cả vật phẩm phần thưởng trên bản đồ.
    - Chế độ "AI Battle!" được thiết kế để các tác nhân tìm kiếm liên tục trong điều kiện các vật phẩm mới được tạo ngẫu nhiên nhằm so sánh giữa các thuật toán với nhau nên các thuật toán không thể tự dừng.
- **Tập hành động (Actions)**: tập các hành động mà tác tử có thể thực hiện để chuyển từ trạng thái này sang trạng thái khác, cụ thể là di chuyển lên, xuống, trái, phải.
- **Mô hình chuyển tiếp (Transition Model)**: chức năng của từng hành động, kết quả của hành động tại một trạng thái cụ thể.
- **Chi phí đường đi (Path Cost)**: hàm tính chi phí cho mỗi đường đi. Để đơn giản, mỗi bước di chuyển của tác nhân sẽ tăng chi phí lên 1.
- **Giải pháp (Solution)**: chuỗi các hành động dẫn từ trạng thái ban đầu đến trạng thái đích, tức là đường đi để nhặt được combo vật phẩm.
- **Giải pháp tối ưu (Best Solution)**: giải pháp có chi phí thấp nhất, đường đi ngắn nhất để lấy được các vật phẩm tạo combo.

##### Breadth-First Search (BFS):
- Duyệt theo bề rộng, mở rộng tất cả các trạng thái lân cận cùng mức trước khi chuyển sang mức sâu hơn.
- Open List: hàng đợi.
- max_depth = 20.

<div style="text-align: center;">
  <img src="DOANAI/gif/Thêm file gif vào đây"/>
</div>

##### Depth-First Search (DFS):
- Ưu tiên mở rộng theo chiều sâu, đi theo một nhánh cho đến khi không thể đi tiếp.
- Open List: Ngăn xếp.
- max_depth = 50.

<div style="text-align: center;">
  <img src="DOANAI/gif/Thêm file gif vào đây"/>
</div>

#### 2.2. Các thuật toán Tìm kiếm có thông tin (Informed Search Algorithms)

Đại diện cho nhóm thuật toán này A*.

##### Thành phần chính của bài toán tìm kiếm
- **Hàm đánh giá f(N)** cho mỗi bước đi để đánh giá mức độ phù hợp của bước di đi đó.
- **Hàm ước lượng chi phí (heuristic) h(N)** không âm (nếu bằng không N là node đích)

##### A* Search:
- Sử dụng hàm đánh giá f(N) = g(N) + h(N)
    - g(N) = chi phí từ node gốc cho đến node hiện tại N, tức là số bước đi tính từ vị trí xuất phát.
    - h(N) = chi phí ước lượng từ nút hiện tại n tới đích. Trong bối cảnh đồ án, hàm h(N) được tính bằng khoảng cách từ vị trí hiện tại đến vật phẩm phần thưởng (*_calculate_heuristic*)
    - f(N) = chi phí tổng thể ước lượng của đường đi qua nút hiện tại N đến đích.
- Open List: hàng đợi ưu tiên
- max_depth = 20.

<div style="text-align: center;">
  <img src="DOANAI/gif/Thêm file gif vào đây"/>
</div>

#### 2.3. Các thuật toán Tìm kiếm cục bộ (Local Search Algorithms)

Trong đồ án, Simulated Annealing được sử dụng làm đại diện cho nhóm thuật toán tìm kiếm cục bộ, nhằm tăng khả năng tìm thấy lời giải trong bài toán.

##### Thành phần chính của bài toán tìm kiếm
- **Trạng thái hiện tại**
- **Trạng thái lân cận (Hàng xóm)**
- **Hàm đánh giá:**
  - Hàm tính khoảng cách Manhattan dựa trên vị trí hiện tại và vị trí vật phẩm (*_calculate_manhattan_distance*).
  - Hàm tính giá trị của trạng thái dựa trên khả năng tạo combo và khoảng cách đến vật phẩm mục tiêu gần nhất (*_evaluate_state*) 
- **Các biến để tính nhiệt độ:**
  - initial_temp: nhiệt độ ban đầu, nhiệt độ cao để ưu tiên khám phá.
  - cooling_rate và iterations_per_temp: sau mỗi iterations_per_temp bước làm lạnh theo tỉ lệ cooling_rate.
  - min_temp: nhiệt độ thấp nhất. Nếu đã giảm nhiệt độ xuống thấp hơn min_temp mà vẫn không tìm được đường đi thì trả về đường đi đến trạng thái tốt nhất.
##### Simulated Annealing
- Thuật toán chọn ngẫu nhiên một lân cận trong tập trạng thái lận cận sinh ra từ bốn hướng di chuyển, tính giá trị của trạng thái đó và xét xem có nhận trạng thái đó không. Nếu trạng thái được chọn tạo được combo, trạng thái đó có điểm rất cao và trả về kết quả. Nếu không tính điểm dựa trên khoảng cách đến các vật phẩm lân cận (ưu tiên loại vật phẩm đã có trong túi). Nếu không còn vật phẩm mục tiêu, trừ điểm và chọn vật phẩm loại khác gần nhất.
- Về cơ chế nhiệt độ, nhiệt độ ban đầu cao để ưu tiên khám phá nhiều trạng thái khác, sau đó giảm dần mỗi chu kì số bước theo tỉ lệ nhất định để tập trung đi tìm lời giải.
- max_depth = 50.

<div style="text-align: center;">
  <img src="DOANAI/gif/Thêm file gif vào đây"/>
</div>

#### 2.4. Các thuật toán Tìm kiếm trong môi trường phức tạp (Complex Environment)

Đối với nhóm tìm kiếm trong môi trường phức tạp, thuật toán Search in Nondeterministic Environment với AND-OR Search được chọn. Tuy nhiên, với môi trường trò chơi này, thuật toán Search in Nondeterministic không phù hợp lắm vì trò chơi chỉ gồm các hướng lên, xuống, trái, phải với trạng thái sinh ra là cố định, bất biến.

##### Thành phần chính của bài toán tìm kiếm
- **Không gian trạng thái bao gồm:**
  - Vị trí hiện tại của tác tử (x, y)
  - Trạng thái túi: danh sách các vật phẩm đã thu thập
  - Danh sách các vật phẩm còn lại trên bản đồ: objects
- **Hàm đánh giá (heuristic):** được thiết kế để ưu tiên trạng thái gần đạt combo, đường đi ngắn đến vật phẩm mục tiêu và tránh các vật phẩm không liên quan. Có hình phạt cho việc đi gần vật phẩm không cần thiết.

##### Search in Nondeterministic Environment
- Cấu trúc tìm kiếm: AND-OR TREE. 
Mỗi trạng thái là một nút trong cây AND-OR, có thể là OR-node (chọn hành động), hoặc AND-node (đạt nhiều điều kiện như combo).
- Sử dụng Heuristic đánh giá "tầm gần" đến combo hoặc điểm tốt nhất. 
- Khi đang tìm combo của một loại bánh, hệ thống buộc phải thu thêm loại đó lần nữa để tạo combo (AND). Khi không còn loại bánh đó thì chuyển sang chọn bất kỳ loại bánh nào gần nhất(OR).
- Chiến lược kết hợp AO: kết hợp giữa heuristic A* và cấu trúc rẽ nhánh logic của AND-OR search. Bản chất AND-OR Search sẽ sinh ra nhiều nhánh trong cây AND-OR, khi áp dụng vào đồ án sẽ gây quá tải bộ nhớ. Việc kết hợp AO* (với hàm heuristic) góp phần giải quyết bùng nổ bộ nhớ và tìm ra được lời giải tốt ưu trong thời gian tốt hơn.
- max_depth = 50

<div style="text-align: center;">
  <img src="DOANAI/gif/Thêm file gif vào đây"/>
</div>

#### 2.5. Các thuật toán Tìm kiếm thỏa mãn ràng buộc (Constraint Satisfaction Problem)

Backtracking with Forward Checking là sự lựa chọn giúp làm tăng khả năng tìm ra lời giải của nhóm thuật toán tốt hơn so với Backtracking thông thường. 

##### Thành phần chính của bài toán tìm kiếm
- **Biến:** mỗi bước di chuyển hoặc mỗi ô trên bản đồ.
- **Miền giá trị:** hành động di chuyển theo bốn hướng lên, xuống, trái, phải hoặc việc chọn vật phẩm phần thưởng.
- **Ràng buộc:** 
  - Chỉ được di chuyển trong lưới, không ra ngoài.
  - Không được đi vào ô trống.
  - Túi chỉ chứa tối đa 7 vật phẩm (bánh).
  - Combo chỉ được tạo khi đủ số vật phẩm giống nhau liên tiếp.
- **Hàm *_reconstruct_path*:** truy vết ngược lại đường đi từ điểm hiện tại *current_pos* về điểm xuất phát dựa trên thông tin từ *came_from*.
- **Forward Checking với hàm *_is_promising*:** kiểm tra sớm xem một trạng thái hiện tại có khả năng dẫn tới một combo hợp lệ hay không, trước khi mở rộng trạng thái đó trong quá trình backtracking.

##### Backtracking with Forward Checking
- Backtracking: duyệt tất cả các hướng đi hợp lệ từ vị trí hiện tại để tìm được combo.
- Forward Checking: trước khi mở rộng trạng thái tiếp theo, kiểm tra xem trạng thái đó có tiềm năng dẫn đến một combo hay không.
- Nếu trong phạm vi *max_depth* không tìm thấy combo fallback với A* để tìm vật phẩm theo quy tắc: túi rỗng thì tìm vật phẩm gần nhất tùy ý, túi có vật phẩm thì tìm vật phẩm cùng loại với vật phẩm vừa thêm gần đây nhất. Nếu trên bản đồ không còn loại đó thì mới tìm loại tùy ý gần nhất.
- max_depth = 70

<div style="text-align: center;">
  <img src="DOANAI/gif/Thêm file gif vào đây"/>
</div>

#### 2.6. Các thuật toán Tìm kiếm học tăng cường (Reinforcement Learning)

Q-Learning là thuật toán dễ tiếp cận hơn với người mới so với những thuật toán học tăng cường khác.

##### Thành phần chính của bài toán tìm kiếm
- **Q-Table:** sử dụng cấu trúc dữ liệu từ diển (dictionary) để lưu trữ giá trị Q cho từng trạng thái–hành động.
- **Công thức cập nhật giá trị Q chuẩn:**
new_q = (1 - $\alpha$) * current_q + $\alpha$ * (reward + $\gamma$ * max_future_q)
- **Chiến lược chọn hành động:** epsilon-greedy.
- **Huấn luyện qua nhiều episode với vòng lặp:**
``` Python
for episode in range(MAX_EPISODES):
```
- **Hàm phần thưởng *_calculate_reward***

##### Q-Learning 
- Khi gọi *_get_valid_actions* đồng thời kết hợp logic “chỉ di chuyển vào ô nhặt được vật phẩm nếu nó phù hợp chiến lược combo $\to$ không cần học phải tránh nhặt sai loại, vì ngay từ đầu những hành động đó đã bị loại bỏ.
- Hàm phần thưởng thiết kế khá chi tiets để khuyến khích agent:
  - Nhặt vật phẩm (thưởng +15)
  - Nhặt cùng loại với item cuối túi (thưởng thêm +20)
  - Tạo combo (thưởng lớn, tỉ lệ points/5)
  - Tiến gần vật phẩm mục tiêu (thưởng +4 / +3)
  - Phạt: đi vòng vo, đi xa mục tiêu, đứng yên…
- Cập nhật Q‑table theo epsilon‑greedy nhằm cân bằng giữa khám phá và khai thác.
- Nếu Q‑table còn quá nhỏ (<200 trạng thái), gọi *_train_q_learning* qua nhiều episodes để thêm kinh nghiệm vào table. Khi đã học xong, *_q_find_combo* tận dụng Q‑table để chọn hành động tốt nhất, kết hợp với BFS nếu thiếu thông tin, để tìm đường dẫn đến combo trong max_depth bước.
- max_depth = 20.

<div style="text-align: center;">
  <img src="DOANAI/gif/Thêm file gif vào đây"/>
</div>

#### 2.7. Chế độ AI Battle

<div style="text-align: center;">
  <img src="DOANAI/gif/BattleAI.png"/>
</div>

- Chế độ này cho phép chọn tối đa ba agent và chọn cho chúng các loại thuật toán khác nhau để so sánh. Môi trường trò chơi liên tục thả các vật phẩm phần thưởng (bánh) theo vị trí ngẫu nhiên.
- Nếu vật phẩm đó bị agent khác nhặt trong khi đang trên đường đến lấy vật phẩm đó thì tính toán lại đường đi khác.
- Nếu hai hoặc ba agent cùng nhặt một vật phẩm thì:
  - Lưu các agent xung đột trong một mảng thứ tự.
  - So sánh thời gian tính toán thuật toán của mỗi agent bị xung đột, nếu cả agent có thời gian tính toán 0.000000s thì thực hiện cộng thêm một phần rất nhỏ *random.uniform(0,99) / 1000000* để làm nhiễu.
  - Đối chiếu với index của mảng xung đột để chỉ ra agent được chọn.
- Thả ngẫu vật phẩm sau mỗi X bước:
  - Nếu có 1 agent thì thả sau 150 bước, hai agent thì 100 sau bước, ba agent thì 50 sau bước.
  - Nếu có quá 20 vật phẩm trên bản đồ, mà đạt số bước thì không thả.
  - Nếu vật trên bản đồ bị giảm đến 5 trong khi chưa đủ số bước thì thả ngẫu nhiên.

## 3. KẾT LUẬN
- "Cake Collect Game" là một môi trường mô phỏng trò chơi lưới 25×25, nơi tác tử di chuyển để thu thập bánh và xâu chuỗi combo tối ưu. Dự án tích hợp và so sánh sáu nhóm thuật toán:
  - Tìm kiếm mù: BFS, DFS.
  - Tìm kiếm cục bộ:Simulated Annealing.
  - Tìm kiếm trong môi trường phức tạp: Search in Nondeterministic Environment.
  - Tìm kiếm có định hướng: A*.
  - Tìm kiếm thỏa mãn ràng buộc: Backtracking with Forward Checking.
  - Học tăng cường: Q‑Learning.

- Mỗi thuật toán được chạy trong chức năng "AI Battle!" trên hàng loạt bản đồ ngẫu nhiên, đo lường hiệu quả về điểm số và thời gian chạy. Kết quả cho thấy:
  - A* hoạt động tốt trên môi trường tĩnh, cấu trúc rõ ràng.
  - Reinforcement Learning (Q‑Learning) cần thời gian huấn luyện nhưng linh hoạt, thích nghi với nhiều tình huống.
  - Thuật toán mù/cục bộ phù hợp với bản đồ nhỏ, ít biến động.
  - Giao diện người dùng đơn giản, trực quan, cho phép quan sát quá trình ra quyết định, lịch sử di chuyển và điểm số.

- Định hướng phát triển
  - Mở rộng luật chơi: thêm vật phẩm đặc biệt, chướng ngại, tác tử phản diện, giới hạn thời gian.
  - So sánh tốc độ giải: ưu tiên thuật toán nhanh hơn trong "AI Battle!".
  - Thuật toán nâng cao: Deep Q‑Network, Monte Carlo Tree Search, phương pháp Deep Learning.
  - Nền tảng đa dạng: phát triển bản web hoặc di động để trực tiếp tương tác và so sánh.
  - Tối ưu hiệu năng & trực quan hóa: giảm thời gian xử lý, cải tiến giao diện hiển thị.

