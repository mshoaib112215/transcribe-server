<?php
$hostname = 'localhost';
// $hostname = '16.170.23.81';
// $username = 'root';
$username = 'centoscpanel_noteclimber';
$password = '';
$password = 'g]#!)9fE7rrR';
$database = 'centoscpanel_noteclimber';
// $database = 'noteclimber';

// Create connection
$conn = new mysqli($hostname, $username, $password, $database);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}
// Function to get user by username
function login($conn, $email, $password)
{
    $query = $conn->prepare("SELECT * FROM users WHERE email = ? and pwd = ?");
    $query->bind_param("ss", $email, $password);
    $query->execute();
    $result = $query->get_result();

    if ($result->num_rows > 0) {
        $row = $result->fetch_assoc();
        $filteredData = userDTO($row); // Filtering out sensitive data
        $access_token = generateAccessToken(); // Generate access token
        $session_info = [
            "access_token" => $access_token,
            "user_info" => $filteredData
        ];
        $session_info_json = json_encode($session_info); // Convert session info to JSON format

        header('Content-Type: application/json');
        echo json_encode($filteredData);
    } else {
        $response = array('error' => 'Email or Password is incorrect');
        header('Content-Type: application/json');
        echo json_encode($response);
    }
}
function updateTrans($conn, $trans_id, $new_trans, $status)
{
    // first get the previous value of the transcriptions then append the new value and updat it remember transcription is an array so append like push in to it
    // $new_trans = $_POST['new_trans'];
    // $new_trans = json_decode($new_trans, true);

    try {
        // Prepare the query
        $query = $conn->prepare("SELECT transcriptions FROM transcriptions_tbl WHERE id = ?");
        $query->bind_param("i", $trans_id);
        $query->execute();
        $result = $query->get_result();
        $row = $result->fetch_assoc();
        $prev_trans = json_decode($row['transcriptions'], true); // decode the JSON string to a PHP array

        // append the new transcriptions to the previous array
        $new_trans = json_decode($new_trans, true); // decode the JSON string to a PHP array
        $prev_trans = array_merge($prev_trans, $new_trans);

        // encode the merged array back to a JSON string
        $prev_trans = json_encode($prev_trans);

        // Prepare the update query
        $query = $conn->prepare("UPDATE transcriptions_tbl SET transcriptions = ?, status = ? WHERE id = ?");
        $query->bind_param("ssi", $prev_trans, $status, $trans_id);
        $query->execute();
        echo "success";
    } catch (Exception $e) {
        // Print the error message
        print_r($conn->error);
    }
}

function generateAccessToken()
{
    return bin2hex(random_bytes(16));
}

function userDto($userData)
{
    // Add logic here to filter out sensitive data from the user object
    $filteredData = array(
        'id' => $userData['id'],
        'name' => $userData['name'],
        'email' => $userData['email'],
    );

    return $filteredData;
}

function sessionChecker()
{
    print_r($_COOKIE);
    exit;
    if (isset($_COOKIE['session_info'])) {
        header('HTTP/1.1 200 OK');
        $session_info = $_COOKIE['session_info'];
        $data = json_decode($session_info, true);
        echo json_encode($data["user_info"]);
        exit;
    } else {
        header('HTTP/1.1 400 Bad Request');
        print_r($_COOKIE);
        echo json_encode(array('error' => 'Session information not found'));
        exit;
    }
}
function handleApiRequest($conn)
{
    // Get the request method and path
    $method = $_SERVER['REQUEST_METHOD'];
    $path = $_SERVER['REQUEST_URI'];
    header('Access-Control-Allow-Origin: *');
    // header('Access-Control-Allow-Origin: http://127.0.0.1:3000');
    // header('Access-Control-Allow-Origin: http://localhost:3000');
    header('Access-Control-Allow-Credentials: true');
    header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type');

    if ($method == 'POST' && $path == '/noteclimberConnection.php/api/checkSession') {
        sessionChecker();
        // echo "hello world";

        exit;
    }
    if (
        $method == 'POST' && $path == '/noteclimberConnection.php/api/update-status-whole-trans'
    ) {
        $status = $_POST['status'];
        $row_id = $_POST['row_id'];

        if (!$status || !$row_id) {
            header('HTTP/1.1 400 Bad Request');
            echo json_encode(array('error' => 'Missing required fields'));
            exit;
        }

        // Prepare and execute SQL statement to update the status field
        $smtp = $conn->prepare("UPDATE audio_book_info SET status=? WHERE row_id=?");
        $smtp->bind_param("si", $status, $row_id);
        $smtp->execute();

        // Check if the update was successful
        if ($smtp->affected_rows > 0) {
            // Update successful, return a success response
            header('HTTP/1.1 200 OK');
            echo "success";
        } else {
            // Update failed, return an error response
            header('HTTP/1.1 500 Internal Server Error');
            echo json_encode(array('error' => 'Failed to update status'));
        }

        exit;
    }

    if (
        $method == 'POST' && $path == '/noteclimberConnection.php/api/store-whole-trans'
    ) {
        // Get the raw data of the request
        $user_id = $_POST['user_id'];
        $trans = $_POST['trans'];
        $row_id = $_POST['row_id'];
        $audio_book_name = $_POST['audio_book_name'];
        if (!$user_id || !$trans || !$audio_book_name || !$row_id) {
            header('HTTP/1.1 400 Bad Request');
            echo json_encode(array('error' => 'Missing required fields'));
            exit;
        }

        // Prepare and execute SQL statement to update the row based on row_id
        $smtp = $conn->prepare("UPDATE audio_book_info SET user_id=?, transcription=?, audio_book_name=? WHERE row_id=?");
        $smtp->bind_param("issi", $user_id, $trans, $audio_book_name, $row_id);
        $smtp->execute();

        // Check if the update was successful
        if ($smtp->affected_rows > 0) {
            // Update successful, return a success response
            header('HTTP/1.1 200 OK');
            echo "success";
        } else {
            // Update failed, return an error response
            header('HTTP/1.1 500 Internal Server Error');
            echo json_encode(array('error' => 'Failed to update row'));
        }

        exit;
    }

    if (
        $method == 'POST' && $path == '/noteclimberConnection.php/api/check-stored-whole-trans'
    ) {
        $audio_book_name = $_POST['audio_book_name'];
        if (!$audio_book_name) {
            header('HTTP/1.1 400 Bad Request');
            echo json_encode(array('error' => 'Missing required fields'));
            exit;
        }

        // Prepare and execute SQL statement to select the row
        $smtp = $conn->prepare("SELECT * FROM audio_book_info WHERE audio_book_name LIKE ?");
        $audio_book_name = "%" . $audio_book_name . "%";
        $smtp->bind_param("s", $audio_book_name);
        $smtp->execute();

        // Get the result
        $result = $smtp->get_result();

        if ($result->num_rows > 0) {
            $row = $result->fetch_assoc();
            $transcription = $row['transcription'];
            $status = $row['status'];

            // Check if the status is 'Completed'
            if ($status == "Completed") {
                // Return status 200 and the transcription if status is 'Completed'
                header('HTTP/1.1 200 OK');
                echo json_encode(array('transcription' => $transcription));
            } else {
                // Return status 400 if status is not 'Completed'
                header('HTTP/1.1 400 Bad Request');
                echo json_encode(array('error' => 'Status is not completed'));
            }
        } else {
            // Return status 400 if no matching row is found
            header('HTTP/1.1 400 Bad Request');
            echo json_encode(array('error' => 'No matching row found'));
        }
        exit;
    }

    if (
        $method == 'GET' && $path == '/noteclimberConnection.php/api/get-whole-trans'
    ) {

        $audio_book_name = $_POST['audio_book_name'];
        if (!$audio_book_name) {
            header('HTTP/1.1 400 Bad Request');
            echo json_encode(array('error' => 'Missing required fields'));
            exit;
        }

        $smtp = $conn->prepare("SELECT * FROM audio_book_info WHERE audio_book_name LIKE ?");
        $audio_book_name = "%" . $audio_book_name . "%";
        $smtp->bind_param("s", $audio_book_name);
        $smtp->execute();

        $result = $smtp->get_result();
        if ($result->num_rows > 0) {
            $row = $result->fetch_assoc();

            header('HTTP/1.1 200 OK');
            echo json_decode($row['transcription'], true);
        } else {

            header('HTTP/1.1 400 Bad Request');
            echo "not found any transcription";
            exit;
        }
        exit;
    }
    if (
        $method == 'GET' && $path == '/noteclimberConnection.php/api/get-all-whole-trans'
    ) {
        // Prepare and execute SQL statement to select all rows
        $smtp = $conn->prepare("SELECT * FROM audio_book_info ");
        $smtp->execute();

        // Get the result
        $result = $smtp->get_result();

        if ($result->num_rows > 0) {
            // Fetch all rows into an array
            $rows = array();
            while ($row = $result->fetch_assoc()) {
                $rows[] = $row;
            }

            // Return status 200 and the array of rows as JSON
            header('HTTP/1.1 200 OK');
            echo json_encode($rows);
        } else {
            // Return status 400 if no rows are found
            header('HTTP/1.1 400 Bad Request');
            echo json_encode(array('error' => 'No transcriptions found'));
        }
        exit;
    }

    if (
        $method == 'POST' && $path == '/noteclimberConnection.php/api/update-trans'
    ) {
        // Get the raw data of the request

        $trans_id = $_POST['trans_id']; // Assuming transcription is initially an empty array
        $new_trans = $_POST['new_trans'];
        $status = $_POST['status'];


        // Check if required parameters are provided
        if (!$new_trans || !$status) {
            header('HTTP/1.1 400 Bad Request');
            echo json_encode(array('error' => 'Missing trans_id'));
            exit;
        }

        updateTrans($conn, $trans_id, $new_trans, $status);
        exit;
    }

    if ($method == 'POST' && $path == '/noteclimberConnection.php/api/reserver-whole-trans') {
        // Get the raw data of the request
        $trans_id = $_POST['trans_id'];
        $new_trans = $_POST['new_trans'];
        $status = $_POST['status'];
        if (!$trans_id || !$new_trans || !$status) {
            header('HTTP/1.1 400 Bad Request');
            echo json_encode(array('error' => 'Missing trans_id'));
            exit;
        }
        print_r($new_trans);

        updateTrans($conn, $trans_id, $_POST['new_trans'], $status);
        exit;
    }
    if ($method == 'POST' && $path == '/noteclimberConnection.php/api/login') {
        // Validate email format
        if (!isset($_POST['email']) || !isset($_POST['password'])) {
            header('HTTP/1.1 400 Bad Request');
            echo json_encode(array('error' => 'Missing email or password'));
            exit;
        }

        $email = $_POST['email'];
        // if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        //     header('HTTP/1.1 400 Bad Request');
        //     echo json_encode(array('error' => 'Invalid email format'));
        //     exit;
        // }

        $password = md5($_POST['password']);
        if (!$password) {
            header('HTTP/1.1 400 Bad Request');
            echo json_encode(array('error' => 'Invalid password'));
            exit;
        }

        login($conn, $email, $password);
        exit;
    }

    if ($method == 'POST' && $path == '/noteclimberConnection.php/api/store-trans') {
        $audio_book_name = $_POST['file_name'] ?? null;
        $transcription = $_POST['transcriptions'] ?? null;
        $user_id = $_POST['user_id'] ?? null;
        $pdfText = $_POST['pdfText'] ?? null;
        $bookName = $_POST['bookName'] ?? null;
        $timestamps = $_POST['time_stamps'] ?? null;

        header('HTTP/1.1 200 OK');

        if ($audio_book_name === null || $transcription === null || $user_id === null || $pdfText === null || $bookName == null || $timestamps === null) {
            header('HTTP/1.1 400 Bad Request');
            echo json_encode(array('error' => 'Missing required fields'));
            echo json_encode(array('error' => array($audio_book_name, $transcription, $user_id, $pdfText, $timestamps, $bookName)));
            exit;
        }

        $status = "Queue";

        // Check if the book already exists in the books_info table
        $stmt = $conn->prepare("SELECT * FROM `books_info` WHERE LOWER(`book_name`) LIKE ? AND `user_id` = ?");
        $searchTerm = "%" . strtolower($bookName) . "%";
        $stmt->bind_param("si", $searchTerm, $user_id);
        $stmt->execute();
        $bookInfo = $stmt->get_result()->fetch_assoc();

        if ($bookInfo) {
            // Book already exists, use the existing book_id
            $book_id = $bookInfo['id'];
        } else {
            // Book does not exist, insert the books_info and get the new book_id
            $stmt = $conn->prepare("INSERT INTO `books_info` (`book_name`, `book_text`, `user_id`) VALUES (?, ?, ?)");
            $stmt->bind_param("ssi", $bookName, $pdfText, $user_id);
            $stmt->execute();
            $book_id = $stmt->insert_id;
        }

        // Insert the transcriptions and get the new trans_id
        $stmt = $conn->prepare("INSERT INTO `transcriptions_tbl` (`audio_book_name`, `transcriptions`, `user_Id`,`status`) VALUES (?, ?, ?,?)");
        $stmt->bind_param("ssis", $audio_book_name, $transcription, $user_id, $status);
        $stmt->execute();
        $trans_id = $stmt->insert_id;

        if ($stmt->error) {
            header('HTTP/1.1 500 Internal Server Error');
            echo json_encode(array('error' => $stmt->error));
            exit;
        }

        $response = ($stmt->affected_rows > 0) ? array("insert_id" => $stmt->insert_id) : "Failed";

        // Insert the timestamps
        $stmt = $conn->prepare("INSERT INTO `timestamps_book_tbl` (`timestamps`, `trans_id`, `user_id`, `book_id`) VALUES (?, ?, ?, ?)");
        $stmt->bind_param("siii", $timestamps, $trans_id, $user_id, $book_id);
        $stmt->execute();

        $stmt->close();

        header('Content-Type: application/json');
        echo json_encode(array('response' => $response));
    }
    if ($method == 'GET' && $path == '/noteclimberConnection.php/api/get-trans') {
        try {
            $stmt = $conn->prepare("SELECT t.*, ts.*, b.book_name, b.book_text FROM `transcriptions_tbl` t JOIN `timestamps_book_tbl` ts ON t.id = ts.trans_id JOIN `books_info` b ON ts.book_id = b.id");
            $stmt->execute();
            $result = $stmt->get_result();

            $transcriptions = array();
            while ($row = $result->fetch_assoc()) {
                $transcriptions[] = array(
                    'id' => $row['id'],
                    'audio_book_name' => $row['audio_book_name'],
                    'transcriptions' => $row['transcriptions'],
                    'user_Id' => $row['user_Id'],
                    'timestamps' => $row['timestamps'],
                    'book_name' => $row['book_name'],
                    'book_text' => $row['book_text'],
                    'user_id' => $row['user_id'],
                    'status' => $row['status'],
                );
            }
            $stmt->close();

            header('HTTP/1.1 200 OK');
            header('Content-Type: application/json');

            echo json_encode($transcriptions);
            exit;
        } catch (Exception $e) {
            header('HTTP/1.1 500 Internal Server Error');
            echo json_encode(array('error' => $e->getMessage()));
            exit;
        }
    }
    if ($method == 'POST' && $path == '/noteclimberConnection.php/api/store-timestamps') {

        $timestamps = $_POST['timestamps'] ?? '';
        $trans_id = $_POST['trans_id'] ?? '';
        $user_id = $_POST['user_id'] ?? '';
        $book_text = $_POST['book_text'] ?? '';

        $stmt = $conn->prepare("INSERT INTO `timestamps_book_tbl` (`timestamps`, `trans_id`, `user_id`) VALUES (?, ?, ?)");
        $stmt->bind_param("siis", $timestamps, $trans_id, $user_id, $book_text);
        try {
            $stmt->execute();
        } catch (Exception $e) {
            header('HTTP/1.1 500 Internal Server Error');
            echo json_encode(array('error' => $e->getMessage()));
            exit;
        }
    }


    // Return a 404 Not Found response for all other requests
    header('HTTP/1.1 404 Not Found');
    exit;
}

handleApiRequest($conn);
