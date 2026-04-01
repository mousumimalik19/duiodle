import OutCall "http-outcalls/outcall";
import Text "mo:core/Text";

actor {
  public query func transform(input : OutCall.TransformationInput) : async OutCall.TransformationOutput {
    OutCall.transform(input);
  };

  // Use v1 endpoint — gemini-2.5-flash is not available on v1beta
  let geminiApiUrlBase = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent";

  let systemContextPrompt = "You are a Vision-to-Code parser. Translate this hand-drawn sketch into a unique JSON UI layout.";
  let userPrompt =
    "Analyze this hand-drawn UI sketch. Detect all UI elements: buttons, inputs, cards, navbars, headings, images, text blocks, icons, containers. For each detected element: identify its type, read any handwritten text/labels inside it (OCR), determine its bounding box position. Map everything to a 1000x1000 coordinate system (top-left is 0,0). Return ONLY raw JSON with this exact schema: {\"sketch_id\": \"unique_hash\", \"detected_elements\": [{\"component\": \"string (button|input|card|nav|image|text|icon|container|heading)\", \"bounds\": {\"x\": int, \"y\": int, \"w\": int, \"h\": int}, \"content\": \"string_or_null\", \"children\": [recursive_elements]}], \"analysis\": {\"layout_type\": \"string\", \"confidence\": float, \"detected_components\": [string], \"auto_improvements\": [string]}}. Output ONLY raw JSON. No markdown, no explanation.";

  func buildRequestBody(imageBase64 : Text, mimeType : Text) : Text {
    "{" #
    "\"contents\": [{" #
    "\"parts\": [" #
    "{" #
    "\"inline_data\": {" #
    "\"mime_type\": \"" # mimeType # "\"," #
    "\"data\": \"" # imageBase64 # "\"" #
    "}" #
    "}," #
    "{" # "\"text\": \"" # systemContextPrompt # "\"" # "}," #
    "{" # "\"text\": \"" # userPrompt # "\"" # "}" #
    "]" #
    "}]" #
    "}";
  };

  public shared ({ caller }) func analyzeSketch(imageBase64 : Text, mimeType : Text, apiKey : Text) : async Text {
    if (imageBase64 == "" or mimeType == "" or apiKey == "") {
      return "{\"error\": \"Missing required parameter. Please provide valid input.\"}";
    };

    let fullApiUrl = geminiApiUrlBase.concat("?key=") # apiKey;
    let requestBody = buildRequestBody(imageBase64, mimeType);

    let extraHeaders : [OutCall.Header] = [{
      name = "Content-Type";
      value = "application/json";
    }];

    let response : Text = await OutCall.httpPostRequest(fullApiUrl, extraHeaders, requestBody, transform);

    if (response.contains(#text "error")) {
      "{\"backend_error\": \"Failed to process sketch\", \"details\": " # response # "}";
    } else {
      response;
    };
  };

  // Health check — returns "ok" when canister is running
  public query func healthCheck() : async Text {
    "ok";
  };

  public query func getInfo() : async {
    appName : Text;
    tagline : Text;
  } {
    {
      appName = "Duiodle";
      tagline = "Turn sketches into code with Gemini Vision";
    };
  };
};
